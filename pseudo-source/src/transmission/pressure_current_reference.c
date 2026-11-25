#include "control.h"
#include "../emissions/egr_internal.h"

/* $BE5C..$BEBB. Hysteresis selects one of two temperature/pressure surfaces.
 * $014D feeds the fast current calculation on subsequent interrupts. */
PcmStatus pcm_pressure_current_reference(Pcm *pcm)
{
    uint8_t flags, value = 0, command;
    SYS_RUN(pcm_read8(pcm, 0x99, &flags));
    if (!(flags & 8u)) {
        uint8_t temp, span, previous;
        SYS_RUN(pcm_read8(pcm, 0xb5, &temp));
        unsigned coordinate = 255u;
        if (temp < 128u) {
            coordinate = 2u * temp;
            SYS_RUN(pcm_read8(pcm, 0xb5, &temp));
            coordinate += temp;
        }
        SYS_RUN(sys_curve16(pcm, coordinate > 255u ? 255u : (uint8_t)coordinate, 0x70a1, &span));
        SYS_RUN(pcm_read8(pcm, 0x147, &previous));
        if (previous >= span) {
            SYS_RUN(pcm_read8(pcm, 0xe2, &command));
            if (previous - span > command) goto falling;
        }
        SYS_RUN(pcm_read8(pcm, 0x147, &previous));
        if ((unsigned)previous + span <= 255u) {
            SYS_RUN(pcm_read8(pcm, 0xe2, &command));
            if (previous + span < command) goto rising;
        }
        SYS_RUN(pcm_read8(pcm, 0x8e, &flags));
        uint16_t surface;
        if (flags & 0x40u) {
rising:
            SYS_RUN(pcm_update8(pcm, 0x8e, 0, 0x40));
            surface = 0x6e59;
        } else {
falling:
            SYS_RUN(pcm_update8(pcm, 0x8e, 0x40, 0));
            surface = 0x6f7d;
        }
        SYS_RUN(pcm_read8(pcm, 0xe2, &command));
        coordinate = 2u * command + (((uint16_t)command * 170u) >> 8);
        SYS_RUN(pcm_read8(pcm, 0xb5, &temp));
        SYS_RUN(egr_surface(pcm, temp, coordinate > 255u ? 255u : (uint8_t)coordinate, surface, &value));
    }
    SYS_RUN(pcm_write8(pcm, 0x14d, value));
    SYS_RUN(pcm_read8(pcm, 0xe2, &command));
    return pcm_write8(pcm, 0x147, command);
}
