#include "resident_input_private_3.h"

PcmStatus pcm_resident_input_b018(Pcm *pcm)
{
    uint8_t a,b,limit,temp,index;
    uint16_t old;
    bool manual,range_fault,range;
    SYS_RUN(pcm_read8(pcm,0x9f,&a));
    SYS_RUN(pcm_write8(pcm,0xa0,a));
    SYS_RUN(test(pcm,0x5d02,0x20,&manual));
    if(manual) {
        SYS_RUN(test(pcm,0x98,4,&range_fault));
        if(!range_fault) {
            SYS_RUN(test(pcm,0xa2,2,&range));
            if(range) {
                SYS_RUN(pcm_write8(pcm,0x9f,0));
                return pcm_update8(pcm,0x9f,0,4);
            }
        }
    }
    SYS_RUN(pcm_read16(pcm,0x1a2,&old));
    SYS_RUN(pcm_read8(pcm,0x1a1,&temp));
    SYS_RUN(pcm_read8(pcm,0x5d2a,&a));
    old=pcm_lag8(temp,old,a);
    SYS_RUN(pcm_write16(pcm,0x1a2,old));
    a=(uint8_t)(old>>8);
    SYS_RUN(pcm_read8(pcm,0x5d2c,&limit));
    if(a<limit) {
        SYS_RUN(pcm_read8(pcm,0x5d2b,&limit));
        index=a<limit?0:1;
    } else {
        SYS_RUN(pcm_read8(pcm,0x5d2d,&limit));
        if(a<limit) index=2;
        else {
            SYS_RUN(pcm_read8(pcm,0x5d2e,&limit));
            index=a<limit?3:4;
        }
    }
    SYS_RUN(pcm_read8(pcm,0xb084u+index,&a));
    SYS_RUN(pcm_read8(pcm,0x1a4,&b));
    if(a!=b) SYS_RUN(pcm_write8(pcm,0x1a5,0));
    else {
        SYS_RUN(pcm_read8(pcm,0x1a5,&b));
        SYS_RUN(pcm_read8(pcm,0x5d29,&limit));
        if(b>=limit) SYS_RUN(pcm_write8(pcm,0x9f,a));
        else if((uint8_t)(b+1u)) SYS_RUN(pcm_write8(pcm,0x1a5,(uint8_t)(b+1u)));
    }
    return pcm_write8(pcm,0x1a4,a);
}
