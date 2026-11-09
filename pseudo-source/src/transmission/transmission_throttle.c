#include "board_io.h"
#include "reference_math.h"
#include "../system/system_internal.h"
/* B0E4..B1AB. The two overlapping history-word copies happen in source
 * order; the second LDD's high byte is the ensuing lag8 target. */
PcmStatus pcm_transmission_throttle(Pcm *pcm)
{
    uint8_t flags,a,b;uint16_t old,value;
    SYS_RUN(pcm_read8(pcm,0x98,&flags));
    if (flags&1u) {
        SYS_RUN(pcm_read8(pcm,0x5b22,&a));
        SYS_RUN(pcm_write16(pcm,0x00b0,(uint16_t)((uint16_t)a*256u)));
        goto publish;
    }
    bool fault=false;
    SYS_RUN(pcm_read8(pcm,0x5b2b,&flags));
    if (flags&1u) {
        SYS_RUN(pcm_read8(pcm,0x5b34,&flags));
        if (!(flags&1u)) { SYS_RUN(pcm_read8(pcm,0x0162,&a));fault=a!=0; }
    }
    if (!fault) {
        SYS_RUN(pcm_read8(pcm,0x5b2c,&flags));
        if (flags&0x80u) {
            SYS_RUN(pcm_read8(pcm,0x5b35,&flags));
            if (!(flags&0x80u)) { SYS_RUN(pcm_read8(pcm,0x0163,&a));fault=a!=0; }
        }
    }
    if (fault) {
        SYS_RUN(pcm_read8(pcm,0x5d02,&flags));
        if (!(flags&1u)) goto publish;
        SYS_RUN(pcm_read8(pcm,0x01aa,&a));
        goto filter;
    }
    SYS_RUN(pcm_read8(pcm,0x00a6,&a));SYS_RUN(pcm_read8(pcm,0x02f6,&b));
    if (a<=b) {
        SYS_RUN(pcm_read16(pcm,0x02f6,&old));
        SYS_RUN(sys_lag16(pcm,(uint16_t)((uint16_t)a*256u+128u),old,0x5b25,&value));
        SYS_RUN(pcm_write16(pcm,0x02f6,value));
    }
    SYS_RUN(pcm_read8(pcm,0x00f7,&a));SYS_RUN(pcm_read8(pcm,0x00d7,&b));
    bool borrow=a<b;a=(uint8_t)(a-b);
    if (borrow) SYS_RUN(sys_update(pcm,0x9a,4,0));
    else {
        SYS_RUN(pcm_read8(pcm,0x9a,&flags));
        if (flags&4u) goto speed_snapshot;
        SYS_RUN(pcm_read8(pcm,0x18,&flags));
        if (flags&2u) goto speed_snapshot;
        SYS_RUN(pcm_read8(pcm,0x18,&flags));
        if (flags&1u) goto speed_snapshot;
        SYS_RUN(pcm_read8(pcm,0x9c,&flags));
        if (!(flags&1u)) goto speed_snapshot;
        SYS_RUN(pcm_read8(pcm,0x5b2a,&b));
        if (a<=b) goto history;
        SYS_RUN(pcm_read8(pcm,0x02f6,&a));SYS_RUN(pcm_read8(pcm,0x5b29,&b));a=(uint8_t)(a+b);
        SYS_RUN(pcm_read8(pcm,0x5b24,&b));
        if (a>b) SYS_RUN(pcm_read8(pcm,0x5b24,&a));
        SYS_RUN(pcm_write8(pcm,0x02f6,a));SYS_RUN(sys_update(pcm,0x9a,0,4));
    }
speed_snapshot:
    SYS_RUN(pcm_read8(pcm,0x00d7,&a));SYS_RUN(pcm_write8(pcm,0x00f7,a));
history:
    SYS_RUN(pcm_read16(pcm,0x01a8,&value));SYS_RUN(pcm_write16(pcm,0x01a9,value));
    SYS_RUN(pcm_read16(pcm,0x01a6,&value));SYS_RUN(pcm_write16(pcm,0x01a7,value));a=(uint8_t)(value>>8);
filter:
    SYS_RUN(pcm_read16(pcm,0x00b0,&old));SYS_RUN(pcm_read8(pcm,0x5b28,&b));
    SYS_RUN(pcm_write16(pcm,0x00b0,pcm_lag8(a,old,b)));
publish:
    SYS_RUN(pcm_read8(pcm,0x00b0,&a));a=(uint8_t)(a-128u);
    SYS_RUN(pcm_read8(pcm,0x0101,&b));
    unsigned sum=(unsigned)a+b;uint8_t result=(uint8_t)sum;
    if (((uint8_t)~(a^b)&(a^result)&0x80u)!=0) result=(uint8_t)(127u+(sum>255u));
    SYS_RUN(pcm_write8(pcm,0x00b2,(uint8_t)(result+128u)));
    SYS_RUN(pcm_read8(pcm,0x5d22,&b));SYS_RUN(pcm_read8(pcm,0x9c,&flags));
    if (!(flags&0x10u)) SYS_RUN(pcm_read8(pcm,0x5d21,&b));
    SYS_RUN(sys_update(pcm,0x9c,0x10,0));SYS_RUN(pcm_read8(pcm,0x00b0,&a));
    if (b<a) {
        SYS_RUN(pcm_read8(pcm,0x9f,&flags));
        if (!(flags&4u)) SYS_RUN(sys_update(pcm,0x9c,0,0x10));
    }
    return PCM_OK;
}
