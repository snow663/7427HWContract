#include "control.h"
#include "hardware.h"
/* C514..C56E: raw-index gear addition and current-enable shadow, then an
 * electronic TCC state update and high-command-byte peripheral publication. */
PcmStatus pcm_transmission_outputs(Pcm *pcm)
{
    if (pcm->calibration == NULL || pcm->calibration->transmission == NULL) return PCM_BAD_CONFIGURATION;
    const PcmTransmissionCalibration *cal = pcm->calibration->transmission;
    uint8_t gear = pcm->transmission.selected_gear;
    if (cal->gear_patterns == NULL || gear >= cal->gear_pattern_length) return PCM_BAD_CONFIGURATION;
    uint8_t pattern = cal->gear_patterns[gear];
    pcm->transmission.output_shadow = (uint8_t)(pattern + (pcm->transmission.output_shadow & 0xfcu));
    bool enabled;
    if (pcm->transmission.current_service_enable & 0x40u)
        enabled = (pcm->transmission.current_service_value & 0x40u) != 0;
    else enabled = !(pcm->transmission.inhibit_flags & 0x08u) &&
                   !(pcm->transmission.fault_flags_primary & 0x02u) &&
                   !(pcm->transmission.fault_flags_secondary & 0x80u) &&
                   !pcm->transmission.driver_inhibit && !(pcm->transmission.output_fault_flags & 0x80u);
    if (enabled) pcm->transmission.output_shadow |= 0x20u;
    else pcm->transmission.output_shadow &= (uint8_t)~0x20u;
    if (pcm->calibration->mode_f & 0x40u) return PCM_OK;
    pcm->transmission.tcc_state &= (uint8_t)~0x01u;
    uint16_t command = pcm->transmission.tcc_command;
    if (command > pcm->transmission.tcc_lower_limit && (pcm->transmission.tcc_flags & 0x04u))
        pcm->transmission.tcc_state |= 0x01u;
    return pcm_write16(pcm, PCM_TCC_COMMAND, (uint16_t)(0x7f00u | (command >> 8)));
}
