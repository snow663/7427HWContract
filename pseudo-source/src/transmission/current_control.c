#include "control.h"
#include "../system/system_internal.h"

/* $7C25..$7C34 and $7C56..$7C62. The sign test and optional gain
 * correction are separate factory reads, even for retained RAM. */
static PcmStatus weighted_error(Pcm *pcm, uint8_t error, uint16_t gain_address,
                                int32_t *result)
{
    uint8_t gain, sign;
    SYS_RUN(pcm_read8(pcm, gain_address, &gain));
    uint16_t product = (uint16_t)error * (uint16_t)gain;
    SYS_RUN(pcm_read8(pcm, 0x014f, &sign));
    if (sign & 0x80u) {
        SYS_RUN(pcm_read8(pcm, gain_address, &gain));
        product = (uint16_t)(product - (uint16_t)gain * 256u);
    }
    *result = product < 0x8000u ? (int32_t)product : (int32_t)product - 65536;
    return PCM_OK;
}

static PcmStatus update_current(Pcm *pcm)
{
    uint8_t error, demand;
    int32_t prior, present;
    SYS_RUN(pcm_read8(pcm, 0x014f, &error));
    SYS_RUN(weighted_error(pcm, error, 0x0154, &prior));
    SYS_RUN(pcm_read8(pcm, 0x014d, &demand));
    int difference = (demand > 57u ? 57 : (int)demand) - (int)pcm->fuel.measured_current;
    if (difference < -128) difference = -128;
    if (difference == 1 || difference == -1) difference = 0;
    error = (uint8_t)difference;
    SYS_RUN(pcm_write8(pcm, 0x014f, error));
    SYS_RUN(weighted_error(pcm, error, 0x0153, &present));

    int32_t delta = present - prior;
    if (delta > 32767) delta = 32767;
    if (delta < -32768) delta = -32768;
    /* Two arithmetic right shifts followed by adding the last shifted bit. */
    delta = delta >= -2 ? (delta + 2) / 4 : -((-delta + 1) / 4);
    uint16_t old;
    SYS_RUN(pcm_read16(pcm, 0x0150, &old));
    uint16_t sum = (uint16_t)((int32_t)old + delta);
    if (delta >= 0 && sum > 0x0e00u) sum = 0x0e00u;
    if (delta < 0 && (int32_t)old + delta < 0) sum = 0;
    SYS_RUN(pcm_write16(pcm, 0x0150, sum));
    /* FDIV saturates when numerator >= denominator. The following rounded
     * conversion also saturates when the high byte would roll over. */
    uint32_t scaled = sum >= 0x0e00u ? 65535u : ((uint32_t)sum << 16) / 0x0e00u;
    pcm->runtime.current_output = (uint8_t)(scaled >= 0xff80u ? 255u : (scaled + 128u) >> 8);
    return PCM_OK;
}

/* $7CC4 and $7CFB both use an unsigned wrapping knot difference. */
static PcmStatus battery_threshold(Pcm *pcm, uint16_t base, uint8_t *threshold)
{
    uint8_t high, low, temperature;
    SYS_RUN(pcm_read8(pcm, base + 1u, &high));
    SYS_RUN(pcm_read8(pcm, base, &low));
    SYS_RUN(pcm_read8(pcm, 0x00b5, &temperature));
    uint16_t product = (uint16_t)(uint8_t)(high - low) * (uint16_t)temperature;
    SYS_RUN(pcm_read8(pcm, base, &low));
    *threshold = (uint8_t)(low + ((product + 128u) >> 8));
    return PCM_OK;
}

static PcmStatus count_observation(Pcm *pcm, bool *expired)
{
    uint8_t count, limit;
    SYS_RUN(pcm_read8(pcm, 0x00fc, &count));
    SYS_RUN(pcm_read8(pcm, 0x6e54, &limit));
    count = (uint8_t)(count + 1u);
    *expired = count > limit;
    return pcm_write8(pcm, 0x00fc, *expired ? 0 : count);
}

/* $7C13..$7D20. The ADC producer and $3068 consumer share the named
 * $014E/$014C owners. The current error is also read by diagnostic 73. */
PcmStatus pcm_current_control(Pcm *pcm)
{
    if (pcm->transmission.output_shadow & 0x20u) {
        SYS_RUN(update_current(pcm));
    } else {
        SYS_RUN(pcm_write16(pcm, 0x0150, 0));
        pcm->runtime.current_output = 0;
        SYS_RUN(pcm_write8(pcm, 0x014f, 0));
    }

    uint16_t command;
    uint8_t threshold;
    bool expired;
    if (!(pcm->transmission.output_fault_flags & 0x80u) && !pcm->transmission.driver_inhibit) {
        SYS_RUN(pcm_read16(pcm, 0x0150, &command));
        if (command == 0x0e00u) {
            SYS_RUN(count_observation(pcm, &expired));
            if (expired) {
                SYS_RUN(battery_threshold(pcm, 0x6e55, &threshold));
                if (threshold > pcm->spark.battery_sample) pcm->transmission.driver_inhibit = true;
                else pcm->transmission.output_fault_flags |= 0x80u;
            }
        }
    }
    if (!(pcm->transmission.output_fault_flags & 0x80u) && !pcm->transmission.driver_inhibit) {
        SYS_RUN(pcm_read16(pcm, 0x0150, &command));
        if (command < 0x0e00u) SYS_RUN(pcm_write8(pcm, 0x00fc, 0));
    }
    if (pcm->transmission.driver_inhibit) {
        SYS_RUN(battery_threshold(pcm, 0x6e57, &threshold));
        if (threshold < pcm->spark.battery_sample) {
            SYS_RUN(count_observation(pcm, &expired));
            if (expired) pcm->transmission.driver_inhibit = false;
        }
    }
    return PCM_OK;
}
