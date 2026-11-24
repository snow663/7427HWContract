#include "gear_internal.h"

typedef struct {
    uint8_t speed;
    uint16_t rpm;
    bool valid;
} ShiftThreshold;

/* $0084 records the selected threshold source before testing road speed. */
static PcmStatus mark_source(Pcm *pcm, bool up, uint8_t bit, ShiftThreshold *threshold)
{
    threshold->valid = true;
    return pcm_update8(pcm, 0x0084, 0, up ? bit : (uint8_t)(bit << 4));
}

/* D8F0, D8CE and the kickdown/normal branches at D4FD and D55D.
 * The two directions have the same priority, with different tables
 * and source bits. Only the upshift kickdown path computes an RPM limit. */
static PcmStatus select_threshold(Pcm *pcm, bool up, uint8_t gear, ShiftThreshold *threshold)
{
    uint16_t address, group = up ? 0xd69f : 0xd6ab;
    uint8_t selector, flags;
    bool found;
    *threshold = (ShiftThreshold){0};
    SYS_RUN(pcm_read8(pcm, 0x0080, &selector));
    SYS_RUN(pcm_transmission_descriptor(pcm, up ? 0xd787 : 0xd79b, selector, gear, &address, &found));
    if (found) {
        SYS_RUN(pcm_read8(pcm, address, &threshold->speed));
        if (threshold->speed != 0) return mark_source(pcm, up, 0x08, threshold);
    }
    SYS_RUN(pcm_transmission_threshold_select(pcm, up ? 0xd763 : 0xd775, gear,
                                              &threshold->speed, &found));
    if (found) return mark_source(pcm, up, 0x04, threshold);

    SYS_RUN(pcm_read8(pcm, 0x009c, &flags));
    if (flags & 0x10u) {
        SYS_RUN(pcm_transmission_kickdown_threshold(pcm, group, gear, &threshold->speed, &found));
        if (found) {
            if (up) SYS_RUN(pcm_transmission_kickdown_rpm(pcm, 0xd6b7, gear, &threshold->rpm));
            return mark_source(pcm, up, 0x02, threshold);
        }
    }
    SYS_RUN(pcm_transmission_normal_threshold(pcm, group, gear, &threshold->speed, &found));
    if (found) return mark_source(pcm, up, 0x01, threshold);
    return PCM_OK;
}

static PcmStatus upshift_allowed(Pcm *pcm, ShiftThreshold threshold, bool *allowed)
{
    *allowed = false;
    if (!threshold.valid || threshold.speed == 0xffu) return PCM_OK;
    uint8_t speed, flags;
    uint16_t rpm;
    SYS_RUN(pcm_read8(pcm, 0x00d7, &speed));
    if (threshold.speed > speed) return PCM_OK;
    SYS_RUN(pcm_read8(pcm, 0x0099, &flags));
    if (flags & 0x20u) threshold.rpm = 0;
    SYS_RUN(pcm_read16(pcm, 0x01ac, &rpm));
    *allowed = threshold.rpm <= rpm;
    return PCM_OK;
}

/* D4EB..D69E. Source tracing at 0084 precedes admission, so an
 * unsuccessful upshift and the following downshift may both leave bits. */
PcmStatus pcm_transmission_gear_select(Pcm *pcm)
{
    if (pcm == NULL) return PCM_BAD_CONFIGURATION;
    SYS_RUN(pcm_transmission_d4eb_prefix(pcm));
    uint8_t gear, speed, flags;
    ShiftThreshold threshold = {0};
    bool up = false;
    int step = 0;
    SYS_RUN(pcm_read8(pcm, 0x00d9, &gear));
    if (gear < 3u) {
        SYS_RUN(select_threshold(pcm, true, gear, &threshold));
        SYS_RUN(upshift_allowed(pcm, threshold, &up));
    }
    if (up) {
        step = 1;
    } else {
        threshold.speed = 0;  /* D557 CLRA before the sign test on gear - 1. */
        SYS_RUN(pcm_read8(pcm, 0x00d9, &gear));
        uint8_t column = (uint8_t)(gear - 1u);
        if ((column & 0x80u) == 0) {
            SYS_RUN(select_threshold(pcm, false, column, &threshold));
            if (threshold.valid && threshold.speed != 0) {
                SYS_RUN(pcm_read8(pcm, 0x00d7, &speed));
                if (threshold.speed > speed) step = -1;
            }
        }
    }
    SYS_RUN(pcm_read8(pcm, 0x00d9, &gear));       /* D5A0 ADDB */
    uint8_t proposed = (uint8_t)(gear + step);
    SYS_RUN(pcm_read8(pcm, 0x00d9, &gear));       /* D5A2 CMPB */
    if (proposed != gear) SYS_RUN(pcm_write8(pcm, 0x0187, threshold.speed));
    SYS_RUN(pcm_read8(pcm, 0x0087, &flags));
    bool limited = (flags & 1u) != 0;
    if (!limited) {
        SYS_RUN(pcm_read8(pcm, 0x0098, &flags));
        limited = (flags & 0x80u) != 0;
    }
    if (limited && proposed > 2u) proposed = 2u;
    return pcm_transmission_gear_finalize(pcm, proposed);
}
