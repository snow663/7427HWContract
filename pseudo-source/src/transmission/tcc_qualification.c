#include "gear_internal.h"
#include "hardware.h"

/* Local shorthand for one logical source transaction, in instruction order. */
#define READ(address, value) SYS_RUN(pcm_read8(pcm, (address), &(value)))
#define SET_REASON(address, mask) SYS_RUN(pcm_update8(pcm, (address), 0, (mask)))

/* C514 also writes 008B. Read its named owner and publish each BSET/BCLR
 * separately. A failed store leaves the previously committed owner intact. */
static PcmStatus tcc_state(Pcm *pcm, uint8_t clear, uint8_t set)
{
    uint8_t value = (uint8_t)((pcm->transmission.tcc_state & (uint8_t)~clear) | set);
    SYS_RUN(pcm_write8(pcm, 0x8b, value));
    pcm->transmission.tcc_state = value;
    return PCM_OK;
}

static PcmStatus service_flags(Pcm *pcm, uint8_t clear, uint8_t set)
{
    uint8_t value = (uint8_t)((pcm->transmission.tcc_flags & (uint8_t)~clear) | set);
    SYS_RUN(pcm_write8(pcm, 0x8a, value));
    pcm->transmission.tcc_flags = value;
    return PCM_OK;
}

static PcmStatus save_command(Pcm *pcm, uint16_t command)
{
    SYS_RUN(pcm_write16(pcm, 0x0126, command));
    pcm->transmission.tcc_command = command;
    return PCM_OK;
}

/* Both temperature checks fetch the first threshold even on the path
 * that replaces it with the second one. */
static PcmStatus cold_reason(Pcm *pcm, uint16_t table, uint16_t sensor, uint8_t mask)
{
    uint8_t threshold, value;
    READ(table, threshold);
    if (pcm->transmission.tcc_state & 1u) READ((uint16_t)(table + 1u), threshold);
    READ(sensor, value);
    if (threshold > value) SET_REASON(0x8c, mask);
    return PCM_OK;
}

/* C6BB..C73F. The first word accumulates independent qualification reasons. */
static PcmStatus range_reasons(Pcm *pcm)
{
    uint8_t options, flags;
    SYS_RUN(pcm_write16(pcm, 0x8c, 0));
    READ(0x6ab4, options);
    if ((options & 8u) && (pcm->iac.gear_status & 3u)) {
        READ(0x87, flags);
        if (!(flags & 2u)) SET_REASON(0x8c, 1);
    }
    READ(0x6ab5, options);
    if ((options & 0x20u) && (pcm->iac.gear_status & 4u)) SET_REASON(0x8d, 0x10);
    READ(0x6ab5, options);
    if ((options & 0x40u) && (pcm->iac.gear_status & 8u)) SET_REASON(0x8d, 0x20);
    READ(0x6ab4, options);
    if (options & 0x20u) SYS_RUN(cold_reason(pcm, 0x6ab8, 0xb5, 2));
    READ(0x6ab4, options);
    if (options & 0x40u) SYS_RUN(cold_reason(pcm, 0x6ab6, 0xa9, 4));
    if (pcm->io.brake_active) SET_REASON(0x8c, 8);
    READ(0x6ab4, options);
    if (options & 2u) {
        READ(0x018d, flags);
        if (flags) {
            READ(0x89, flags);
            if (flags & 0x40u) SYS_RUN(tcc_state(pcm, 0, 0x20));
            SET_REASON(0x8c, 0x10);
        }
    }
    READ(0x6ab4, options);
    if (options & 1u) {
        READ(0x018c, flags);
        if (flags) SET_REASON(0x8c, 0x20);
    }
    READ(0x6ab5, options);
    if (options & 0x10u) {
        READ(0x0124, flags);
        if (flags) SET_REASON(0x8d, 1);
    }
    return PCM_OK;
}

static PcmStatus gear_speed_reason(Pcm *pcm)
{
    uint8_t flags, gear, threshold, speed;
    READ(0x87, flags);
    if (flags & 2u) return PCM_OK;
    READ(0x9c, flags);
    if (!(flags & 2u)) return PCM_OK;
    READ(0xd9, gear);
    if (!gear) return PCM_OK;
    READ((uint16_t)(0x6abbu + gear), threshold);
    if (!(pcm->transmission.tcc_state & 1u)) READ((uint16_t)(0x6abeu + gear), threshold);
    READ(0xd7, speed);
    if (threshold > speed) SET_REASON(0x8c, 0x40);
    return PCM_OK;
}

/* E674 uses the resident nine-byte diagnostic mask scan and publishes
 * 0098.6 before C783 reads it. 0089.2 selects the hysteresis threshold. */
static PcmStatus fault_reasons(Pcm *pcm)
{
    uint8_t flags, temperature, threshold, gear;
    SYS_RUN(pcm_transmission_fault_gate_674(pcm));
    READ(0x98, flags);
    if (flags & 0x40u) {
        READ(0x89, flags);
        uint16_t table = flags & 4u ? 0x6ac2 : 0x6ac3;
        READ(0xb5, temperature);
        READ(table, threshold);
        READ(0x89, flags);
        bool warm = temperature > threshold;
        flags = warm ? (uint8_t)(flags | 4u) : (uint8_t)(flags & ~4u);
        SYS_RUN(pcm_write8(pcm, 0x89, flags));
        pcm->transmission.range_context = flags;
        if (!warm) SET_REASON(0x8d, 4);
    }
    READ(0x99, flags);
    if (flags & 4u) {
        READ(0xd9, gear);
        if (gear != 3) SET_REASON(0x8d, 8);
    }
    return PCM_OK;
}

static PcmStatus remaining_reasons(Pcm *pcm)
{
    uint8_t options, flags;
    READ(0x6ab5, options);
    if (options & 2u) SYS_RUN(gear_speed_reason(pcm));
    READ(0x6ab5, options);
    if (options & 1u) {
        READ(0x89, flags);
        if (flags & 0x80u) SET_REASON(0x8c, 0x80);
    }
    READ(0x6ab5, options);
    if ((options & 4u) && (pcm->transmission.tcc_state & 8u)) {
        SYS_RUN(tcc_state(pcm, 8, 0));
        SET_REASON(0x8d, 2);
    }
    READ(0x6ab5, options);
    if (options & 4u) return fault_reasons(pcm);
    return PCM_OK;
}

static PcmStatus command_limit(Pcm *pcm, uint16_t table, uint16_t destination)
{
    uint8_t sample, limit;
    READ(0xe2, sample);
    uint8_t coordinate = sample > 127u ? 255 : (uint8_t)(sample * 2u);
    SYS_RUN(sys_curve16(pcm, coordinate, table, &limit));
    uint16_t value = (uint16_t)((uint16_t)limit << 8);
    SYS_RUN(pcm_write16(pcm, destination, value));
    if (destination == 0x012b) pcm->transmission.tcc_lower_limit = value;
    return PCM_OK;
}

static PcmStatus request_apply(Pcm *pcm)
{
    SYS_RUN(tcc_state(pcm, 2, 0));
    return tcc_state(pcm, 0, 4);
}

static PcmStatus request_release(Pcm *pcm)
{
    SYS_RUN(tcc_state(pcm, 0, 2));
    return tcc_state(pcm, 4, 0);
}

/* C849..C89B. Kickdown selects a scalar. A missing kickdown descriptor
 * falls through to the normal TPS curve. Both paths floor at the first knot. */
static PcmStatus speed_request(Pcm *pcm)
{
    uint8_t flags, selector, gear, threshold = 0, floor, speed;
    uint16_t pointer, corrected;
    bool valid = false;
    READ(0x89, flags);
    uint16_t table = flags & 0x40u ? 0xc31a : 0xc2d6;
    READ(0x9c, flags);
    if (flags & 0x10u) {
        READ(0xd9, gear);
        READ(0x7f, selector);
        SYS_RUN(pcm_transmission_descriptor(pcm, (uint16_t)(table + 0x22u), selector, gear, &pointer, &valid));
        if (valid) {
            READ(pointer, threshold);
            SYS_RUN(pcm_write8(pcm, 0x0128, threshold));
        }
    }
    if (!valid) {
        READ(0x7f, selector);
        READ(0xd9, gear);
        SYS_RUN(pcm_transmission_descriptor(pcm, table, selector, gear, &pointer, &valid));
        if (!valid) return tcc_state(pcm, 6, 0);
        READ(pointer, floor);
        SYS_RUN(pcm_write8(pcm, 0x0128, floor));
        uint8_t throttle;
        READ(0xb2, throttle);
        SYS_RUN(sys_curve16(pcm, throttle, pointer, &threshold));
    }
    READ(0x9c, flags);
    table = flags & 0x10u ? 0xc3f8 : 0xc3e6;
    SYS_RUN(pcm_transmission_temperature_gain(pcm, table, (uint16_t)((uint16_t)threshold << 8), &corrected));
    threshold = (uint8_t)(corrected >> 8);
    READ(0x0128, floor);
    if (threshold < floor) READ(0x0128, threshold);
    READ(0xd7, speed);
    return threshold > speed ? request_release(pcm) : request_apply(pcm);
}

/* C6BB..C8B0. Limit production always precedes service and fault overrides. */
PcmStatus pcm_tcc_qualification(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    SYS_RUN(range_reasons(pcm));
    SYS_RUN(remaining_reasons(pcm));
    SYS_RUN(command_limit(pcm, 0x6d5e, 0x0129));
    SYS_RUN(command_limit(pcm, 0x6d6f, 0x012b));
    uint8_t service = pcm->transmission.service_tcc, flags, gear, limit;
    if (service != 0) {
        if (service <= 100u) {
            SYS_RUN(save_command(pcm, (uint16_t)(652u * service)));
            return service_flags(pcm, 0, 0x14);
        }
        if (pcm->transmission.tcc_flags & 0x10u) SYS_RUN(service_flags(pcm, 0x14, 0));
        return service <= 200u ? request_apply(pcm) : request_release(pcm);
    }
    READ(0x99, flags);
    if (flags & 8u) {
        SYS_RUN(save_command(pcm, 0));
        return tcc_state(pcm, 6, 0);
    }
    if (pcm->transmission.tcc_flags & 0x10u) SYS_RUN(service_flags(pcm, 0x14, 0));
    READ(0x8c, flags);
    if (!(flags & 8u)) {
        READ(0x8c, flags);
        if (!(flags & 0x20u)) {
            READ(0x99, flags);
            if (flags & 4u) {
                READ(0xd9, gear);
                if (gear == 3) return request_apply(pcm);
            }
        }
    }
    uint16_t reasons;
    SYS_RUN(pcm_read16(pcm, 0x8c, &reasons));
    if (reasons) return tcc_state(pcm, 6, 0);
    READ(0x018e, flags);
    if (flags) return request_release(pcm);
    /* C832 tests whether either live 0018.4/.5 fault is present. C836
     * then requires both bits of the ROM reaction mask. */
    bool bypass = false;
    if (pcm->spark.map_fault || pcm->fuel.oxygen_idle_fault) {
        READ(0x5b2d, flags);
        bypass = (flags & 0x30u) == 0x30u;
    }
    if (!bypass) {
        READ(0x6aec, limit);
        READ(0x89, flags);
        if (!(flags & 0x40u)) READ(0x6aed, limit);
        if (limit > pcm->spark.load_coordinate) return request_release(pcm);
    }
    return speed_request(pcm);
}
