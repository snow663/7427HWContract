#include "resident_input_private_1.h"

/* E5F1..E60A */
PcmStatus pcm_resident_fault_e5f1(Pcm *pcm)
{
    uint8_t a, b;
    SYS_RUN(pcm_read8(pcm, 0x5b2f, &a));
    SYS_RUN(pcm_read8(pcm, 0x1a, &b));
    bool active = (a & b & 0x18u) != 0;
    if (!active) {
        SYS_RUN(pcm_read8(pcm, 0x86, &a));
        if (!(a & 0x80u)) {
            SYS_RUN(pcm_read8(pcm, 0x100, &b));
            active = b == 0;
        }
    }
    return pcm_update8(pcm, 0x99, 8, active ? 8 : 0);
}
