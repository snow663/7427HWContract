#include "board_io.h"
#include "reference_math.h"

/* Stock BMHM C668..C6BA: slot01 speed-source selection. The primary
 * and secondary speed candidates are calibrated words $5B6F/$5B73;
 * the fallback multiplies BARO ADC by $5D07, adds $5D08 and feeds
 * $F436's rounded signed-word lag using gain at $5D0A. Each source
 * bit test is sampled in its own instruction order, not pre-read. */
#define RUN(call) do {PcmStatus result=(call);if(result!=PCM_OK)return result;}while(0)
PcmStatus pcm_speed_source(Pcm *pcm)
{
    if(pcm==NULL)return PCM_BAD_CONFIGURATION;
    uint8_t options,flags,source,word8;
    uint16_t desired,old,offset;
    RUN(pcm_read8(pcm,0x5b30u,&options));
    if(options&4u) {
        RUN(pcm_read8(pcm,0x001bu,&flags));
        if(flags&4u)goto primary;
    }
    RUN(pcm_read8(pcm,0x5b2du,&options));
    if(options&0x20u) {
        RUN(pcm_read8(pcm,0x0018u,&flags));
        if(flags&0x20u) {
            RUN(pcm_read8(pcm,0x5d02u,&source));
            if(!(source&4u))goto primary;
        }
    }
    RUN(pcm_read8(pcm,0x5b30u,&options));
    if(options&2u) {
        RUN(pcm_read8(pcm,0x001bu,&flags));
        if(flags&2u)goto secondary;
    }
    RUN(pcm_read8(pcm,0x5b2du,&options));
    if(options&0x10u) {
        RUN(pcm_read8(pcm,0x0018u,&flags));
        if(flags&0x10u) {
            RUN(pcm_read8(pcm,0x5d02u,&source));
            if(!(source&4u))goto secondary;
        }
    }
    /* C6A5..C6B7: unsigned 8x8, then wrapping 16-bit addition. */
    RUN(pcm_read8(pcm,0x02f3u,&word8));
    RUN(pcm_read8(pcm,0x5d07u,&source));
    desired=(uint16_t)((uint16_t)word8*source);
    RUN(pcm_read16(pcm,0x5d08u,&offset));
    desired=(uint16_t)(desired+offset);
    RUN(pcm_read16(pcm,0x00acu,&old));
    RUN(pcm_read8(pcm,0x5d0au,&source));
    desired=pcm_lag16(desired,old,source,NULL);
    return pcm_write16(pcm,0x00acu,desired);
primary:
    RUN(pcm_read16(pcm,0x5b6fu,&desired));
    return pcm_write16(pcm,0x00acu,desired);
secondary:
    RUN(pcm_read16(pcm,0x5b73u,&desired));
    return pcm_write16(pcm,0x00acu,desired);
}
