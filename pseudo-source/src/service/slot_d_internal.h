#ifndef PCM_SLOT_D_INTERNAL_H
#define PCM_SLOT_D_INTERNAL_H
#include "service.h"
#include "../system/system_internal.h"

/* Most operands are logical RAM or calibration. Live faults produced in C
 * (particularly MAT in this same slot) share the nine-byte reporting bank.
 * Slots 04 and 0F write the transmission faults at the provider's 001C/001D. */
static inline uint8_t d_bit(uint8_t v, uint8_t mask, bool on)
{
    return on ? (uint8_t)(v | mask) : (uint8_t)(v & (uint8_t)~mask);
}

static inline PcmStatus d_read(Pcm *pcm, uint16_t address, uint8_t *out)
{
    uint8_t v;
    SYS_RUN(pcm_read8(pcm, address, &v));
    switch (address) {
    case 0x16: v = pcm->runtime.primary_faults; break;
    case 0x17:
        v = d_bit(v, 0x80, pcm->iac.input_fault);
        v = d_bit(v, 0x40, pcm->io.mat_low_fault);
        v = d_bit(v, 0x10, pcm->io.mat_high_fault);
        break;
    case 0x18:
        v = d_bit(v, 0x20, pcm->fuel.oxygen_idle_fault);
        v = d_bit(v, 0x10, pcm->spark.map_fault);
        v = d_bit(v, 8, pcm->iac.learning_fault);
        v = d_bit(v, 4, pcm->iac.kicker_fault);
        break;
    case 0x19:
        v = d_bit(v, 0x40, pcm->reference.bank_fault);
        v = d_bit(v, 0x20, pcm->spark.est_fault);
        v = d_bit(v, 0x10, pcm->knock.sensor_fault);
        v = d_bit(v, 8, pcm->fuel.oxygen_fault_b);
        v = d_bit(v, 4, pcm->fuel.oxygen_fault_a);
        break;
    case 0x1a:
        v = d_bit(v, 0x20, pcm->runtime.special_fast_group);
        v = d_bit(v, 2, pcm->runtime.adc_timeout);
        break;
    case 0x43:
        v = d_bit(v, 0x10, pcm->fuel.oxygen_changed);
        v = d_bit(v, 0x20, pcm->scheduler.epoch_toggle);
        v = d_bit(v, 0x80, pcm->runtime.first_conversion);
        break;
    case 0x6e: v = d_bit(v, 1, pcm->fuel.asynchronous_active); break;
    case 0x6f: v = pcm->spark.load_status; break;
    case 0x70: v = d_bit(v, 4, pcm->fuel.alternate_interval); break;
    case 0x71: v = d_bit(v, 4, pcm->fuel.oxygen_notification); break;
    case 0x72:
        v = d_bit(v, 0x40, pcm->fuel.alternate_afr_limit);
        v = d_bit(v, 0x80, pcm->runtime.service_output_mirror);
        break;
    default: break;
    }
    *out = v;
    return PCM_OK;
}

static inline PcmStatus d_store(Pcm *pcm, uint16_t address, uint8_t value)
{
    SYS_RUN(pcm_write8(pcm, address, value));
    switch (address) {
    case 0x04: pcm->spark.bypass_supervision = (value & 0x80u) != 0; break;
    case 0x16: pcm->runtime.primary_faults = value; break;
    case 0x18: pcm->fuel.oxygen_idle_fault = (value & 0x20u) != 0; break;
    case 0x19:
        pcm->fuel.oxygen_fault_b = (value & 8u) != 0;
        pcm->fuel.oxygen_fault_a = (value & 4u) != 0;
        break;
    case 0x43: pcm->fuel.oxygen_changed = (value & 0x10u) != 0; break;
    case 0x6e: pcm->fuel.asynchronous_active = (value & 1u) != 0; break;
    case 0x6f: pcm->spark.load_status = value; break;
    case 0x70: pcm->fuel.alternate_interval = (value & 4u) != 0; break;
    case 0x71: pcm->fuel.oxygen_notification = (value & 4u) != 0; break;
    case 0x72:
        pcm->fuel.alternate_afr_limit = (value & 0x40u) != 0;
        pcm->runtime.service_output_mirror = (value & 0x80u) != 0;
        break;
    case 0x223: pcm->io.egr_failure_count = value; break;
    case 0x22c: pcm->spark.bypass_count = value; break;
    default: break;
    }
    return PCM_OK;
}

static inline PcmStatus d_update(Pcm *pcm, uint16_t a, uint8_t clear, uint8_t set)
{
    uint8_t flags;
    SYS_RUN(d_read(pcm, a, &flags));
    return d_store(pcm, a, (uint8_t)((flags & (uint8_t)~clear) | set));
}

static inline PcmStatus d_count(Pcm *pcm, uint16_t a, int increment, uint8_t *after)
{
    uint8_t v;
    SYS_RUN(d_read(pcm, a, &v));
    *after = (uint8_t)(v + increment);
    return d_store(pcm, a, *after);
}

#define D_READ(a, v) SYS_RUN(d_read(pcm, (a), &(v)))
#define D_STORE(a, v) SYS_RUN(d_store(pcm, (a), (v)))
#define D_CLEAR(a, m) SYS_RUN(d_update(pcm, (a), (m), 0))
#define D_SET(a, m) SYS_RUN(d_update(pcm, (a), 0, (m)))
#define D_COUNT(a, n, v) SYS_RUN(d_count(pcm, (a), (n), &(v)))
#endif
