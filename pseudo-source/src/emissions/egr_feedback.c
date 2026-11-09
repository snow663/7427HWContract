#include "control.h"
#include "reference_math.h"
#include "../system/system_internal.h"
/* D14E..D1F5: linear-position acquisition, zero tracking and two lag filters.
 * The post-filter +0080 wraps; a timeout still consumes the ADR4 sample. */
PcmStatus pcm_egr_feedback(Pcm *pcm)
{
    uint8_t flags,sample,high,gain;uint16_t zero,value,old;
    SYS_RUN(pcm_read8(pcm,0x400d,&flags));
    if (!(flags&2u)) return pcm_write8(pcm,0x01b9,0);
    SYS_RUN(pcm_mask_irq(pcm,true));SYS_RUN(pcm_adc_mux(pcm,3));
    SYS_RUN(pcm_adc_convert(pcm,1));SYS_RUN(pcm_mask_irq(pcm,false));
    SYS_RUN(pcm_read8(pcm,PCM_ADR4,&sample));SYS_RUN(pcm_write8(pcm,0x01b4,sample));
    SYS_RUN(pcm_read8(pcm,0x01b5,&high));
    if (sample<high) {
        SYS_RUN(pcm_read16(pcm,0x01b5,&zero));SYS_RUN(pcm_read8(pcm,0x48a7,&gain));
        value=pcm_lag8(sample,zero,gain);high=(uint8_t)(value>>8);
        uint8_t minimum;SYS_RUN(pcm_read8(pcm,0x48a6,&minimum));
        if (high<minimum) {
            SYS_RUN(pcm_read8(pcm,0x48a6,&minimum));value=(uint16_t)((uint16_t)minimum*256u);
        }
        SYS_RUN(pcm_write16(pcm,0x01b5,value));
    }
    SYS_RUN(pcm_read8(pcm,0x01b4,&sample));SYS_RUN(pcm_read16(pcm,0x01b5,&zero));
    value=(uint16_t)((uint16_t)sample*256u+128u);high=value<zero?0:(uint8_t)((value-zero)>>8);
    SYS_RUN(pcm_read8(pcm,0x48a4,&gain));value=(uint16_t)((uint16_t)high*gain);
    if (value>0x3fc0u) value=0x3fc0;
    value=(uint16_t)(value*4u);SYS_RUN(pcm_read16(pcm,0x01b7,&old));
    SYS_RUN(sys_lag16(pcm,value,old,0x48a8,&value));SYS_RUN(pcm_write16(pcm,0x01b7,value));
    high=(uint8_t)((uint16_t)(value+128u)>>8);SYS_RUN(pcm_write8(pcm,0x01b9,high));
    if (high>128u) return sys_update(pcm,0x41,0,1);
    SYS_RUN(pcm_read8(pcm,0x01ae,&sample));
    if (sample!=0) return PCM_OK;
    SYS_RUN(pcm_read8(pcm,0x41,&flags));
    if (!(flags&1u)) return PCM_OK;
    SYS_RUN(sys_update(pcm,0x41,1,0));SYS_RUN(pcm_read8(pcm,0x01b5,&high));high=(uint8_t)(high+2u);
    uint8_t maximum;SYS_RUN(pcm_read8(pcm,0x48a5,&maximum));
    if (high>maximum) SYS_RUN(pcm_read8(pcm,0x48a5,&high));
    return pcm_write8(pcm,0x01b5,high);
}
