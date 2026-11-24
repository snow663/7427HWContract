#ifndef PCM_SERVICE_INTERNAL_H
#define PCM_SERVICE_INTERNAL_H
#include "service.h"
#include "serial.h"
#include "fuel.h"
#define SVC_RUN(call) do { PcmStatus svc_result=(call);if (svc_result!=PCM_OK) return svc_result; } while (0)

/* The clear command owns only the bits its keep mask drops. Apply that mask
 * to native producers after the bus write succeeds, including faults that
 * have not yet appeared in the provider's snapshot. */
static inline PcmStatus svc_write_masked(Pcm *pcm, uint16_t address, uint8_t value, uint8_t keep)
{
    SVC_RUN(pcm_serial_memory_write8(pcm, address, (uint8_t)(value & keep)));
    switch (address) {
    case 0x04:
        if (!(keep & 0x80u)) pcm->spark.bypass_supervision = false;
        break;
    case 0x16:
        pcm->runtime.primary_faults &= keep;
        break;
    case 0x17:
        if (!(keep & 0x80u)) pcm->iac.input_fault = false;
        if (!(keep & 0x40u)) pcm->io.mat_low_fault = false;
        if (!(keep & 0x10u)) pcm->io.mat_high_fault = false;
        break;
    case 0x18:
        if (!(keep & 0x20u)) pcm->fuel.oxygen_idle_fault = false;
        if (!(keep & 0x10u)) pcm->spark.map_fault = false;
        if (!(keep & 8u)) pcm->iac.learning_fault = false;
        if (!(keep & 4u)) pcm->iac.kicker_fault = false;
        break;
    case 0x19:
        if (!(keep & 0x40u)) pcm->reference.bank_fault = false;
        if (!(keep & 0x20u)) pcm->spark.est_fault = false;
        if (!(keep & 0x10u)) pcm->knock.sensor_fault = false;
        if (!(keep & 8u)) pcm->fuel.oxygen_fault_b = false;
        if (!(keep & 4u)) pcm->fuel.oxygen_fault_a = false;
        break;
    case 0x1a:
        if (!(keep & 0x20u)) pcm->runtime.special_fast_group = false;
        if (!(keep & 2u)) pcm->runtime.adc_timeout = false;
        break;
    case 0x1c: pcm->transmission.fault_flags_primary &= keep; break;
    case 0x1d: pcm->transmission.fault_flags_secondary &= keep; break;
    case 0x44:
        if (!(keep & 0x80u)) pcm->spark.bypass_fault_latched = false;
        break;
    case 0x6f: pcm->spark.load_status &= keep; break;
    case 0x8e: pcm->transmission.output_fault_flags &= keep; break;
    default: break;
    }
    return PCM_OK;
}

static inline PcmStatus svc_clear_bits(Pcm *pcm,uint16_t address,uint8_t mask)
{
    uint8_t value;SVC_RUN(pcm_serial_memory_read8(pcm,address,&value));
    return svc_write_masked(pcm, address, value, (uint8_t)~mask);
}
#endif
