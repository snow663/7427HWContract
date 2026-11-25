#include "control.h"
#include "../system/system_internal.h"

static int signed_byte(uint8_t value)
{
    return value < 128u ? (int)value : (int)value - 256;
}

static uint8_t saturate_byte(int value)
{
    if (value > 127) return 127;
    if (value < -128) return 128;
    return (uint8_t)value;
}

/* DECB/ASLB wraps before ABX or ABY. */
static PcmStatus gear_index(Pcm *pcm, uint8_t *index)
{
    SYS_RUN(pcm_read8(pcm, 0xd9, index));
    *index = (uint8_t)(*index - 1u);
    return PCM_OK;
}

static PcmStatus curve_at(Pcm *pcm, uint16_t pointer, uint8_t *result)
{
    uint16_t table;
    uint8_t throttle;
    SYS_RUN(pcm_read16(pcm, pointer, &table));
    SYS_RUN(pcm_read8(pcm, 0xb2, &throttle));
    return sys_curve16(pcm, throttle, table, result);
}

/* $BA65..$BAC2. Record a measured shift even if learning is inhibited. */
static PcmStatus record_shift(Pcm *pcm)
{
    uint8_t baro, limit, flags, desired, age, origin, index;
    SYS_RUN(pcm_update8(pcm, 0x93, 0x7d, 0));
    SYS_RUN(pcm_read8(pcm, 0xac, &baro));
    SYS_RUN(pcm_read8(pcm, 0x68d1, &limit));
    if (baro < limit) SYS_RUN(pcm_update8(pcm, 0x93, 0, 2));
    else {
        SYS_RUN(pcm_read8(pcm, 0x68d2, &limit));
        if (baro > limit) SYS_RUN(pcm_update8(pcm, 0x93, 2, 0));
    }
    SYS_RUN(pcm_read8(pcm, 0x93, &flags));
    uint16_t pointers = (flags & 2u) ? 0xbc47u : 0xbc41u;
    SYS_RUN(pcm_read8(pcm, 0x9f, &flags));
    if (flags & 2u) pointers += 12u;
    SYS_RUN(pcm_read8(pcm, 0x114, &desired));
    if (!desired) {
        SYS_RUN(gear_index(pcm, &index));
        SYS_RUN(curve_at(pcm, pointers + (uint8_t)(index << 1), &desired));
    }
    SYS_RUN(gear_index(pcm, &index));
    SYS_RUN(pcm_read8(pcm, 0xdb, &age));
    SYS_RUN(pcm_read8(pcm, 0xda, &origin));
    uint8_t elapsed = (uint8_t)(age - origin);
    SYS_RUN(pcm_write8(pcm, 0xdc, elapsed));
    SYS_RUN(pcm_write8(pcm, 0x136u + index, elapsed));
    uint8_t error = saturate_byte((int)desired - (int)elapsed);
    SYS_RUN(pcm_write8(pcm, 0xdd, error));
    return pcm_write8(pcm, 0x139u + index, error);
}

/* Select the biased learning step at $BAC3..$BB4D. */
static PcmStatus learning_step(Pcm *pcm, uint8_t *step)
{
    uint8_t flags, index, value, limit;
    SYS_RUN(pcm_read8(pcm, 0x68a8, &flags));
    if (flags & 2u) {
        SYS_RUN(gear_index(pcm, &index));
        SYS_RUN(curve_at(pcm, 0xbc59u + (uint8_t)(index << 1), &limit));
        SYS_RUN(gear_index(pcm, &index));
        SYS_RUN(pcm_read8(pcm, 0x19cu + index, &value));
        if (value != 255u && value > limit) {
            SYS_RUN(pcm_update8(pcm, 0x93, 0, 0x10));
            SYS_RUN(gear_index(pcm, &index));
            return pcm_read8(pcm, 0x69adu + index, step);
        }
    }
    SYS_RUN(gear_index(pcm, &index));
    SYS_RUN(pcm_read8(pcm, 0x68a8, &flags));
    if (!(flags & 1u)) {
        SYS_RUN(pcm_read8(pcm, 0xda, &value));
        SYS_RUN(pcm_read8(pcm, 0x69a7u + index, &limit));
        if (value < limit) goto error_step;
        SYS_RUN(pcm_read8(pcm, 0xb5, &value));
        SYS_RUN(pcm_read8(pcm, 0x69a5, &limit));
        if (value <= limit) goto error_step;
        SYS_RUN(pcm_read8(pcm, 0xb2, &value));
        SYS_RUN(pcm_read8(pcm, 0x69a6, &limit));
        if (value > limit) {
            SYS_RUN(pcm_update8(pcm, 0x93, 0, 4));
            return pcm_read8(pcm, 0x69aau + index, step);
        }
    }
error_step:
    SYS_RUN(pcm_read8(pcm, 0xdd, &value));
    SYS_RUN(pcm_read8(pcm, 0x699fu + index, &limit));
    if (signed_byte(value) < signed_byte(limit)) {
        SYS_RUN(pcm_update8(pcm, 0x93, 0, 8));
        return pcm_read8(pcm, 0x69a2u + index, step);
    }
    SYS_RUN(pcm_update8(pcm, 0x93, 0, 0x20));
    SYS_RUN(gear_index(pcm, &index));
    uint16_t table;
    SYS_RUN(pcm_read16(pcm, 0xbc3bu + (uint8_t)(index << 1), &table));
    SYS_RUN(pcm_read8(pcm, 0xdd, &value));
    int coordinate = signed_byte(value) + 8;
    if (coordinate < 0) coordinate = 0;
    if (coordinate > 16) coordinate = 16;
    return pcm_read8(pcm, (uint16_t)(table + coordinate), step);
}

/* $BB9D..$BBEB. Carry after SUBB #5 suppresses the negative cap.
 * The low-bit phase at $00DE participates in both headroom caps. */
static PcmStatus weighted_step(Pcm *pcm, uint8_t *out)
{
    uint8_t offset, weight, biased, room, phase;
    SYS_RUN(pcm_read8(pcm, 0x14b, &offset));
    SYS_RUN(pcm_read8(pcm, 0x6a16u + offset, &weight));
    SYS_RUN(pcm_read8(pcm, 0xe1, &biased));
    int delta = (int)biased - 128;
    unsigned magnitude = (unsigned)(delta < 0 ? -delta : delta);
    uint8_t rounded = (uint8_t)((magnitude * weight + 128u) >> 8);
    *out = delta < 0 ? (uint8_t)(0u - rounded) : rounded;
    if (delta < 0 && !rounded) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, delta < 0 ? 0xdf : 0xe0, &room));
    if (!room) *out = 0;
    else if (room < 16u) {
        SYS_RUN(pcm_read8(pcm, 0xde, &phase));
        uint8_t bound = (uint8_t)((delta < 0 ? -8 : 8) * (int)room + phase);
        if (delta < 0) {
            if (bound >= 5u && *out < (uint8_t)(bound - 5u)) *out = (uint8_t)(bound - 5u);
        } else if (*out > bound) *out = bound;
    }
    return PCM_OK;
}

/* $BB65..$BC3A. The ROM reloads the bank pointer after every committed
 * cell. A skipped low coordinate leaves X at the current bank base. */
static PcmStatus learn_cells(Pcm *pcm)
{
    uint8_t index, offset, coordinate, cell, phase, step, limit, flags;
    uint16_t bank;
    SYS_RUN(gear_index(pcm, &index));
    uint16_t pointers = (uint16_t)(0xbc65u + (uint8_t)(index << 1));
    SYS_RUN(pcm_read16(pcm, pointers, &bank));
    SYS_RUN(pcm_write8(pcm, 0x14b, 0));
    for (;;) {
        SYS_RUN(pcm_read8(pcm, 0x14b, &offset));
        if (offset > 4u) return PCM_OK;
        SYS_RUN(pcm_read8(pcm, 0x149, &coordinate));
        coordinate = (uint8_t)(coordinate + offset);
        if (coordinate > 18u) return PCM_OK;
        if (coordinate >= 2u) {
            uint16_t address = (uint16_t)(bank + coordinate - 2u);
            SYS_RUN(pcm_read8(pcm, address, &cell));
            phase = (uint8_t)(((cell - 128u) ^ 9u) & 7u);
            SYS_RUN(pcm_write8(pcm, 0xde, phase));
            SYS_RUN(weighted_step(pcm, &step));
            SYS_RUN(pcm_read8(pcm, address, &cell));
            int next = signed_byte(saturate_byte((int)cell - 128 + signed_byte(step)));
            SYS_RUN(curve_at(pcm, pointers + 12u, &limit));
            if (next < (int)limit - 128) next = (int)limit - 128;
            SYS_RUN(curve_at(pcm, pointers + 6u, &limit));
            if (next > (int)limit - 128) next = (int)limit - 128;
            SYS_RUN(pcm_read8(pcm, 0x113, &flags));
            if (flags) return PCM_OK;
            SYS_RUN(pcm_read8(pcm, 0x86, &flags));
            if (!(flags & 8u)) return PCM_OK;
            uint8_t checksum;
            SYS_RUN(pcm_read8(pcm, address, &cell));
            SYS_RUN(pcm_read8(pcm, 0x32b, &checksum));
            uint8_t updated = (uint8_t)(next + 128);
            SYS_RUN(pcm_mask_irq(pcm, true));
            SYS_RUN(pcm_write8(pcm, address, updated));
            SYS_RUN(pcm_write8(pcm, 0x32b, (uint8_t)(checksum + cell - updated)));
            SYS_RUN(pcm_mask_irq(pcm, false));
        }
        SYS_RUN(pcm_read8(pcm, 0x14b, &offset));
        SYS_RUN(pcm_write8(pcm, 0x14b, (uint8_t)(offset + 1u)));
        if (coordinate >= 2u) SYS_RUN(pcm_read16(pcm, pointers, &bank));
    }
}

PcmStatus pcm_shift_adaptive_learning(Pcm *pcm)
{
    SYS_RUN(record_shift(pcm));
    uint8_t step, flags, reasons, other;
    SYS_RUN(learning_step(pcm, &step));
    SYS_RUN(pcm_write8(pcm, 0xe1, step));
    SYS_RUN(pcm_read8(pcm, 0x93, &flags));
    if (!(flags & 4u)) {
        SYS_RUN(pcm_read8(pcm, 0x93, &flags));
        if (!(flags & 0x38u)) return PCM_OK;
        SYS_RUN(pcm_read8(pcm, 0x91, &reasons));
        SYS_RUN(pcm_read8(pcm, 0x90, &other));
        reasons |= other;
        SYS_RUN(pcm_read8(pcm, 0x92, &other));
        if (reasons | other) return PCM_OK;
    }
    SYS_RUN(pcm_update8(pcm, 0x93, 0, 1));
    return learn_cells(pcm);
}
