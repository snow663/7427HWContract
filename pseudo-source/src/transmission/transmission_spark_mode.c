#include "control.h"
#include "../system/system_internal.h"

/* $DA34..$DA6E. Entry and retention have separate thresholds and
 * comparison senses. Sample each pair only when the ROM reaches it. */
static PcmStatus range_hysteresis(Pcm *pcm, bool *clear_range)
{
    uint8_t speed, throttle, limit;
    uint16_t rpm, rpm_limit;
    SYS_RUN(pcm_read8(pcm, 0xd7, &speed));
    SYS_RUN(pcm_read8(pcm, 0x70c2, &limit));
    if (speed < limit) {
        SYS_RUN(pcm_read16(pcm, 0x1ac, &rpm));
        SYS_RUN(pcm_read16(pcm, 0x70bf, &rpm_limit));
        if (rpm > rpm_limit) {
            SYS_RUN(pcm_read8(pcm, 0xb2, &throttle));
            SYS_RUN(pcm_read8(pcm, 0x70c1, &limit));
            if (throttle > limit) {
                pcm->spark.transmission_status |= 4u;
                return PCM_OK;
            }
        }
    }
    SYS_RUN(pcm_read8(pcm, 0xd7, &speed));
    SYS_RUN(pcm_read8(pcm, 0x70be, &limit));
    if (speed > limit) goto clear;
    SYS_RUN(pcm_read16(pcm, 0x1ac, &rpm));
    SYS_RUN(pcm_read16(pcm, 0x70c3, &rpm_limit));
    if (rpm < rpm_limit) goto clear;
    SYS_RUN(pcm_read8(pcm, 0xb2, &throttle));
    SYS_RUN(pcm_read8(pcm, 0x70c5, &limit));
    if (throttle >= limit) return PCM_OK;
clear:
    *clear_range = true;
    return PCM_OK;
}

/* $D9B7..$D9EE. Compare the live range with the previous sample at $A3. */
static PcmStatus range_entry(Pcm *pcm)
{
    uint8_t range, previous, options, speed, limit;
    SYS_RUN(pcm_read8(pcm, 0xa2, &range));
    if (range & 15u) {
        SYS_RUN(pcm_read8(pcm, 0xa3, &previous));
        if (!(previous & 15u)) goto enter;
    }
    SYS_RUN(pcm_read8(pcm, 0xa2, &range));
    if (!(range & 32u)) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0xa3, &previous));
    if (previous & 32u) return PCM_OK;
enter:
    pcm->spark.transmission_status |= 1u;
    pcm->spark.transmission_status &= (uint8_t)~0x12u;
    SYS_RUN(pcm_write8(pcm, 0x15d, 0));
    SYS_RUN(pcm_read8(pcm, 0xa2, &range));
    if (!(range & 32u)) {
        SYS_RUN(pcm_read8(pcm, 0x70d4, &options));
        if (!(options & 1u)) goto cancel;
    }
    uint8_t gear = pcm->transmission.selected_gear;
    if (gear == 3u || gear == 2u) goto cancel;
    SYS_RUN(pcm_read8(pcm, 0xd7, &speed));
    SYS_RUN(pcm_read8(pcm, 0x70d3, &limit));
    if (speed <= limit) return PCM_OK;
cancel:
    pcm->spark.transmission_status &= (uint8_t)~1u;
    return PCM_OK;
}

/* $D9F3..$DA32. $015D saturates by suppressing the wrapping store. */
static PcmStatus active_range(Pcm *pcm)
{
    uint16_t rpm, rpm_limit;
    uint8_t age, throttle, limit;
    SYS_RUN(pcm_read8(pcm, 0x15d, &age));
    if (age != 255u) SYS_RUN(pcm_write8(pcm, 0x15d, age + 1u));
    SYS_RUN(pcm_read16(pcm, 0x1ac, &rpm));
    SYS_RUN(pcm_read16(pcm, 0x70b8, &rpm_limit));
    if (rpm <= rpm_limit) {
        SYS_RUN(pcm_read8(pcm, 0xb2, &throttle));
        SYS_RUN(pcm_read8(pcm, 0x70ba, &limit));
        if (throttle <= limit) goto test_exit;
    }
    pcm->spark.transmission_status |= 2u;
    pcm->spark.transmission_status &= (uint8_t)~1u;
test_exit:
    SYS_RUN(pcm_read16(pcm, 0xc2, &rpm));
    SYS_RUN(pcm_read16(pcm, 0x70bb, &rpm_limit));
    if (rpm >= rpm_limit) {
        SYS_RUN(pcm_read8(pcm, 0x15d, &age));
        SYS_RUN(pcm_read8(pcm, 0x70bd, &limit));
        if (age <= limit) return PCM_OK;
    }
    if (pcm->spark.transmission_status & 2u) {
        pcm->spark.transmission_status |= 16u;
        SYS_RUN(pcm_read8(pcm, 0x70d2, &limit));
        SYS_RUN(pcm_write8(pcm, 0x15e, limit));
    }
    pcm->spark.transmission_status &= (uint8_t)~3u;
    return PCM_OK;
}

PcmStatus pcm_transmission_spark_mode(Pcm *pcm)
{
    bool clear_range = false;
    SYS_RUN(range_entry(pcm));
    if (pcm->spark.transmission_status & 3u) {
        SYS_RUN(active_range(pcm));
    } else {
        SYS_RUN(range_hysteresis(pcm, &clear_range));
    }
    uint8_t range;
    if (!clear_range) {
        SYS_RUN(pcm_read8(pcm, 0xa2, &range));
        clear_range = (range & 0x50u) != 0;
    }
    if (clear_range) pcm->spark.transmission_status &= (uint8_t)~4u;
    return PCM_OK;
}
