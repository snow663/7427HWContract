#include "board_io.h"
/* D4A3..D4D9. ASLD wraps; FDIV overflow/divide-by-zero returns FFFF.
 * The first observation only seeds the previous timestamp. */
PcmStatus pcm_vss_calculate(Pcm *pcm)
{
    uint8_t count=pcm->io.vss_changes,age=pcm->io.vss_age;
    if (!count) {
        if (age) --age;
        if (!age) pcm->io.vss_raw=0;
    } else {
        if (age) {
            uint16_t numerator=(uint16_t)(460u*count);
            uint16_t denominator=(uint16_t)(pcm->io.vss_timestamp-pcm->io.vss_previous);
            pcm->io.vss_raw=numerator>=denominator?UINT16_MAX:
                (uint16_t)(((uint32_t)numerator<<16)/denominator);
        }
        pcm->io.vss_changes=0;pcm->io.vss_previous=pcm->io.vss_timestamp;age=0x27;
    }
    pcm->io.vss_age=age;return PCM_OK;
}
