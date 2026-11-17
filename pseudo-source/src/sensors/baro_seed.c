#include "board_io.h"
#include "../system/system_internal.h"
/* C614..C667 is an interior boot entry: it does not acquire/filter MAP. */
PcmStatus pcm_baro_seed(Pcm *pcm)
{
    uint8_t value;SYS_RUN(pcm_read8(pcm,0x02f4,&value));
    if (value==0) {
        SYS_RUN(pcm_read8(pcm,0x4e68,&value));
        SYS_RUN(pcm_write8(pcm,0x02f3,value));
        SYS_RUN(pcm_write16(pcm,0x02f4,(uint16_t)((uint16_t)value*256u)));
    }
    value=value<13u?143u:(uint8_t)(((uint16_t)(value-13u)*151u+128u)>>8);
    SYS_RUN(pcm_write8(pcm,0x01cc,value));
    static const uint16_t tables[]={0x4b60,0x4c89,0x4975,0x49d1};
    static const uint16_t outputs[]={0x01e4,0x01e3,0x01cd,0x01ce};
    for (unsigned i=0;i<4;++i) {
        if (i!=0) SYS_RUN(pcm_read8(pcm,0x01cc,&value));
        uint8_t result;SYS_RUN(sys_curve16(pcm,value<96u?0:(uint8_t)(value-96u),tables[i],&result));
        SYS_RUN(pcm_write8(pcm,outputs[i],result));
    }
    return PCM_OK;
}
