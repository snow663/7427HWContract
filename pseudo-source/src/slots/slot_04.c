#include "scheduler.h"
#include "control.h"
#include "board_io.h"
#include "../system/system_internal.h"

/* Publish each RMW separately so the governor's 006F.4 and the other
 * load-status owners survive, even if a later transaction fails. */
static PcmStatus publish_load_bits(Pcm *pcm, uint8_t clear, uint8_t set)
{
    SYS_RUN(pcm_update8(pcm, 0x6f, clear, set));
    pcm->spark.load_status = (uint8_t)((pcm->spark.load_status & (uint8_t)~clear) | set);
    return PCM_OK;
}

/* 7AC7..7B02. Sample the phase only after the common diagnostic group. */
PcmStatus pcm_slot_04(Pcm *pcm)
{
    if (pcm == NULL || pcm->platform == NULL) return PCM_BAD_CONFIGURATION;
    SYS_RUN(pcm_diagnostic_slot_04(pcm));
    if (pcm->scheduler.phase & 0x10u) {
        SYS_RUN(pcm_transmission_adaptive_reset(pcm));
        SYS_RUN(pcm_transmission_adaptive_restore(pcm));
        SYS_RUN(pcm_diagnostic_trans_temp_adc_low(pcm));
        SYS_RUN(pcm_diagnostic_trans_temp_adc_high(pcm));
        SYS_RUN(pcm_transmission_temperature_input(pcm));
        SYS_RUN(pcm_transmission_temperature_filter(pcm));
    } else {
        SYS_RUN(pcm_diagnostic_coolant_adc_low(pcm));
        SYS_RUN(pcm_diagnostic_coolant_adc_high(pcm));
        SYS_RUN(pcm_coolant_input(pcm));
        SYS_RUN(pcm_coolant_filter(pcm));
        SYS_RUN(pcm_environment_inputs(pcm));
    }
    SYS_RUN(publish_load_bits(pcm, 0x24u, 0));
    if (pcm->runtime.primary_faults & 1u) SYS_RUN(publish_load_bits(pcm, 0, 0x04));
    if (pcm->iac.input_fault) SYS_RUN(publish_load_bits(pcm, 0, 0x20));
    return PCM_OK;
}
