#include "board_io.h"
#include "reference_math.h"
/* 7BAA..7BF4. F49A caps before F4BD's fixed16 subtraction. The final
 * fractional-bit rounding wraps the MAP byte when the high byte isFF. */
PcmStatus pcm_map_input(Pcm *pcm)
{
    if (pcm->calibration==NULL || pcm->calibration->io==NULL) return PCM_BAD_CONFIGURATION;
    const PcmIoCalibration *cal=pcm->calibration->io;
    uint8_t target=pcm->reference.map_sample;
    if (pcm->spark.load_status&0x48u) {
        target=cal->map_default;
        if (pcm->runtime.fuel_running) {
            uint32_t product=4u*(uint32_t)cal->map_throttle_gain*pcm->reference.throttle;
            if (product<=65535u) {
                const PcmCappedCurve *curve=&cal->map_bias;
                uint8_t coordinate=pcm->reference.rpm_coordinate>>1;
                if (coordinate>curve->limit) coordinate=curve->limit;
                coordinate=coordinate<16u?0:(uint8_t)(coordinate-16u);
                if (curve->values==NULL || (coordinate>>4)+1u>=curve->length) return PCM_BAD_CONFIGURATION;
                uint16_t requested=(uint16_t)pcm_lookup16(coordinate,curve->values)+(product>>8);
                if (requested<=cal->map_default) target=(uint8_t)requested;
            }
        }
    }
    uint8_t gain=pcm->io.map_transient?cal->map_transient_gain:cal->map_normal_gain;
    uint16_t filtered=pcm_lag8(target,pcm->io.map_filter,gain);
    pcm->io.map_filter=filtered;
    pcm->spark.map_filtered=(uint8_t)((filtered>>8)+((filtered>>7)&1u));
    return PCM_OK;
}
