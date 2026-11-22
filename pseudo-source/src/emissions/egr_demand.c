#include "egr_internal.h"
/* CF16..D03D. Earlier failed gates retain later hysteresis bits. Demand is
 * published before the optional1815 hook and final service override. */
PcmStatus pcm_egr_demand(Pcm *pcm)
{
    uint8_t flags,value,threshold,coordinate,result=0;
    SYS_RUN(pcm_read8(pcm,0x400b,&flags));
    if (flags&0x40u) {
        SYS_RUN(pcm_read8(pcm,0x0230,&value));SYS_RUN(pcm_read8(pcm,0x46fd,&threshold));
        SYS_RUN(pcm_read8(pcm,0x006e,&flags));
        if (!(flags&0x80u)) SYS_RUN(pcm_read8(pcm,0x46fc,&threshold));
        if (value<=threshold) goto publish;
    }
    SYS_RUN(pcm_read8(pcm,0x0282,&value));SYS_RUN(pcm_read8(pcm,0x46f9,&threshold));
    SYS_RUN(pcm_read8(pcm,value<=threshold?0x46fa:0x46fb,&threshold));
    SYS_RUN(pcm_read8(pcm,0x0006,&value));if (threshold>value) goto publish;
    SYS_RUN(pcm_read8(pcm,0x0018,&flags));if (flags&0x30u) goto publish;
    SYS_RUN(pcm_read8(pcm,0x4703,&threshold));SYS_RUN(pcm_read8(pcm,0x006e,&flags));
    if (flags&0x10u) SYS_RUN(pcm_read8(pcm,0x4704,&threshold));
    SYS_RUN(pcm_read8(pcm,0x01c0,&value));
    if (threshold>=value) { SYS_RUN(sys_update(pcm,0x006e,0x10,0));goto publish; }
    SYS_RUN(sys_update(pcm,0x006e,0,0x10));SYS_RUN(pcm_read8(pcm,0x006f,&flags));
    if (!(flags&0x24u)) {
        SYS_RUN(pcm_read8(pcm,0x4701,&threshold));SYS_RUN(pcm_read8(pcm,0x006e,&flags));
        if (flags&0x20u) SYS_RUN(pcm_read8(pcm,0x4702,&threshold));
        SYS_RUN(pcm_read8(pcm,0x01d9,&value));
        if (threshold>=value) { SYS_RUN(sys_update(pcm,0x006e,0x20,0));goto publish; }
        SYS_RUN(sys_update(pcm,0x006e,0,0x20));
    }
    SYS_RUN(pcm_read8(pcm,0x0062,&value));SYS_RUN(pcm_read8(pcm,0x46ff,&threshold));
    SYS_RUN(pcm_read8(pcm,0x006e,&flags));
    if (flags&0x40u) SYS_RUN(pcm_read8(pcm,0x4700,&threshold));
    if (threshold>value) { SYS_RUN(sys_update(pcm,0x006e,0x40,0));goto publish; }
    SYS_RUN(sys_update(pcm,0x006e,0,0x40));SYS_RUN(pcm_read8(pcm,0x0016,&flags));
    if (!(flags&0x10u)) {
        SYS_RUN(pcm_read8(pcm,0x0284,&value));SYS_RUN(pcm_read8(pcm,0x46fe,&threshold));
        if (value<threshold) goto publish;
    }
    SYS_RUN(pcm_read8(pcm,0x4705,&threshold));SYS_RUN(pcm_read8(pcm,0x006e,&flags));
    if (!(flags&4u)) SYS_RUN(pcm_read8(pcm,0x4706,&threshold));
    SYS_RUN(pcm_read8(pcm,0x01c9,&value));
    if (threshold<value) { SYS_RUN(sys_update(pcm,0x006e,4,0));goto publish; }
    SYS_RUN(sys_update(pcm,0x006e,0,4));SYS_RUN(pcm_read8(pcm,0x4707,&threshold));
    SYS_RUN(pcm_read8(pcm,0x01d9,&value));if (threshold<value) goto publish;
    SYS_RUN(pcm_read8(pcm,0x4708,&threshold));SYS_RUN(pcm_read8(pcm,0x024a,&value));
    if (threshold>value) goto publish;
    SYS_RUN(pcm_read8(pcm,0x0046,&flags));if (flags&8u) goto publish;
    SYS_RUN(pcm_read8(pcm,0x400d,&flags));
    if (flags&8u) { SYS_RUN(pcm_read8(pcm,0x003e,&flags));if (!(flags&0x80u)) goto publish; }
    SYS_RUN(pcm_read8(pcm,0x01cf,&coordinate));SYS_RUN(pcm_read8(pcm,0x470a,&value));
    if (value!=2u) {
        SYS_RUN(pcm_read8(pcm,0x01c9,&coordinate));SYS_RUN(pcm_read8(pcm,0x470a,&value));
        if (value!=0) SYS_RUN(pcm_read8(pcm,0x01c0,&coordinate));
    }
    SYS_RUN(pcm_read8(pcm,0x0062,&value));if (value>160u) value=160;
    SYS_RUN(egr_surface(pcm,value,(uint8_t)(coordinate>>1),0x470b,&result));
    SYS_RUN(pcm_read8(pcm,0x01bb,&value));result=egr_double_product(result,value);
    SYS_RUN(pcm_read8(pcm,0x01cc,&coordinate));SYS_RUN(pcm_read8(pcm,0x01c0,&value));
    SYS_RUN(egr_surface(pcm,(uint8_t)(value>>1),coordinate,0x4767,&value));
    result=egr_double_product(result,value);
publish:
    SYS_RUN(pcm_read8(pcm,0x4709,&threshold));
    if (result<threshold) result=0;
    else {
        SYS_RUN(pcm_read8(pcm,0x0051,&flags));
        if (flags&0x10u) result=0;
        else { SYS_RUN(pcm_read8(pcm,0x0072,&flags));if (flags&0x20u) result=0; }
    }
    SYS_RUN(pcm_write8(pcm,0x01ae,result));SYS_RUN(pcm_read8(pcm,0x0086,&flags));
    if (flags&0x40u) {
        if (pcm->platform==NULL || pcm->platform->call_address==NULL) return PCM_NO_HARDWARE;
        SYS_RUN(pcm->platform->call_address(pcm->platform->context,0x1815));
    }
    SYS_RUN(pcm_read8(pcm,0x003b,&flags));if (!(flags&0x10u)) return PCM_OK;
    SYS_RUN(pcm_read8(pcm,0x0393,&flags));if (!(flags&2u)) return PCM_OK;
    SYS_RUN(pcm_read8(pcm,0x0394,&result));return pcm_write8(pcm,0x01ae,result);
}
