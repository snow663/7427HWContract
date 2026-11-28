#include "resident_input_private_3.h"

PcmStatus pcm_resident_input_b1f0(Pcm *pcm)
{
    uint16_t a,b,old,value;
    SYS_RUN(lag_store(pcm,0xb7,0x1ac,0x5d10));
    SYS_RUN(lag_store(pcm,0xbd,0xc2,0x5d14));
    SYS_RUN(lag_store(pcm,0xc4,0xc6,0x5d17));
    SYS_RUN(pcm_read16(pcm,0xb7,&a));
    SYS_RUN(pcm_read16(pcm,0xc4,&b));
    SYS_RUN(pcm_read16(pcm,0xeb,&old));
    SYS_RUN(pcm_resident_lag_f420(pcm,clamp_difference(a,b),old,0x5d0d,&value));
    SYS_RUN(pcm_write16(pcm,0xeb,value));
    return pcm_write16(pcm,0xed,(value&0x8000u)?(uint16_t)(0u-value):value);
}
