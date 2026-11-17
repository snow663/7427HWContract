#include "iac.h"
#include "../system/system_internal.h"
/* 92F1..93C4. Snapshot growth clears a fraction only on the word store.
 * 9343 tests the actual RAM0008 byte, not an immediate option mask. */
PcmStatus pcm_iac_restore(Pcm *pcm)
{
    for (unsigned i=0;i<2;++i) {
        uint8_t flags;SYS_RUN(pcm_read8(pcm,9,&flags));
        uint8_t mask=(uint8_t)(0x10u<<i);
        if (flags&mask) {
            uint16_t snapshot=(uint16_t)(0x02a9u+3u*i),integral=(uint16_t)(snapshot-2u);
            uint8_t value,addition,old;SYS_RUN(pcm_read8(pcm,snapshot,&value));
            SYS_RUN(pcm_read8(pcm,(uint16_t)(0x5098u+i),&addition));
            unsigned sum=(unsigned)value+addition;value=(uint8_t)sum;
            if (sum>255u) SYS_RUN(pcm_read8(pcm,(uint16_t)(0x50c3u+i),&value));
            SYS_RUN(pcm_write8(pcm,snapshot,value));SYS_RUN(pcm_read8(pcm,integral,&old));
            if (value>old) SYS_RUN(pcm_write16(pcm,integral,(uint16_t)((uint16_t)value*256u)));
            SYS_RUN(sys_update(pcm,9,mask,0));
        }
    }
    uint8_t mode;SYS_RUN(pcm_read8(pcm,0x4e90,&mode));
    if (mode&1u) {
        uint8_t value;SYS_RUN(pcm_read8(pcm,0x029f,&value));SYS_RUN(pcm_write8(pcm,0x029d,value));
        SYS_RUN(pcm_read8(pcm,0x02a9,&value));SYS_RUN(pcm_write8(pcm,0x02a7,value));
    }
    uint8_t options,target;SYS_RUN(pcm_read8(pcm,0x4e8f,&options));SYS_RUN(pcm_read8(pcm,8,&target));
    if (options&target) {
        uint8_t coolant,limit;SYS_RUN(pcm_read8(pcm,6,&coolant));SYS_RUN(pcm_read8(pcm,0x4eb5,&limit));
        uint16_t addition_address=coolant<limit?0x4eb4:0x4eb3;
        static const uint16_t sources[]={0x029d,0x029f,0x02a7,0x02a9};
        static const uint16_t destinations[]={0x02a0,0x02a2,0x02aa,0x02ac};
        for (unsigned i=0;i<4;++i) {
            uint8_t base,addition;SYS_RUN(pcm_read8(pcm,sources[i],&base));
            SYS_RUN(pcm_read8(pcm,addition_address,&addition));
            unsigned sum=(unsigned)base+addition;
            if (sum>255u && (i==0 || i==2))
                SYS_RUN(pcm_write8(pcm,(uint16_t)(destinations[i]+1u),255));
            SYS_RUN(pcm_write8(pcm,destinations[i],sum>255u?255:(uint8_t)sum));
        }
    } else {
        SYS_RUN(pcm_read8(pcm,0x4e90,&mode));
        if (mode&1u) {
            uint8_t value;SYS_RUN(pcm_read8(pcm,0x02a2,&value));SYS_RUN(pcm_write8(pcm,0x02a0,value));
            SYS_RUN(pcm_read8(pcm,0x02ac,&value));SYS_RUN(pcm_write8(pcm,0x02aa,value));
        }
    }
    return PCM_OK;
}
