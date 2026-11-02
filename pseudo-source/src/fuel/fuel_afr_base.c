#include "fuel.h"
#include "mixture_internal.h"
#include "reference_math.h"
/* 891E..899A; entry idle state owns the departure-filter initialization. */
PcmStatus pcm_fuel_afr_base(Pcm *pcm)
{
    MIX_CAL();
    uint8_t value = cal->stoich;
    bool closed = (pcm->io.coolant_context & 0xa0u) != 0;
    if (closed) {
        pcm->fuel.commanded_afr = value;
        if (!(pcm->calibration->mode_d & 1u)) return PCM_OK;
    }
    if (!closed || pcm->reference.coolant <= cal->open_coolant) {
        uint8_t column = cal->open_mode ? pcm->spark.load_coordinate : pcm->spark.vacuum;
        MIX_RUN(pcm_lookup2d(mix_min(pcm->reference.coolant, 192), (uint8_t)(column >> 1), &cal->open_afr, &value));
    }
    value = mix_sub(value, pcm->fuel.startup_afr);
    if (pcm->spark.idle_state) {
        value = mix_min(value, pcm->io.environmental_load);
        pcm->fuel.afr_filter_count = 60;
        pcm->fuel.afr_filtered = (uint16_t)((uint16_t)value << 8);
    } else {
        uint8_t count = pcm->fuel.afr_filter_count;
        if (count != 0) --pcm->fuel.afr_filter_count;
        if (count != 0 && value > (pcm->fuel.afr_filtered >> 8)) {
            uint16_t filtered = pcm_lag8(value, pcm->fuel.afr_filtered, cal->afr_filter_gain);
            pcm->fuel.afr_filtered = filtered;
            value = mix_byte(((uint32_t)filtered + 128u) >> 8);
        } else pcm->fuel.afr_filtered = (uint16_t)((uint16_t)value << 8);
    }
    pcm->fuel.commanded_afr = value;
    return PCM_OK;
}
