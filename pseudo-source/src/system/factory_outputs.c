#include "system_internal.h"
/* FACA..FBD6. The captured B/ID survives heartbeat activity. All FBD6
 * call/RTS gaps retain a separate minimum11-cycle backend delay. */
PcmStatus pcm_factory_outputs(Pcm *pcm,uint8_t captured_id)
{
    uint16_t row=0xfc01;uint8_t port;
    bool cycling=false;
    if (captured_id==0) { SYS_RUN(pcm_read8(pcm,0x3064,&port));cycling=(port&0x80u)!=0; }
    if (cycling) {
        SYS_RUN(pcm_write16(pcm,0x3fcc,0xdfff));SYS_RUN(pcm_delay_cycles(pcm,11));
        SYS_RUN(pcm_write16(pcm,0x3fea,0xdfff));SYS_RUN(pcm_delay_cycles(pcm,11));
        SYS_RUN(pcm_write16(pcm,0x3fce,197));SYS_RUN(pcm_delay_cycles(pcm,11));
        SYS_RUN(pcm_write16(pcm,0x3fdc,66));SYS_RUN(pcm_delay_cycles(pcm,11));
        SYS_RUN(pcm_write16(pcm,0x3ff6,0xffec));
        uint8_t phase;SYS_RUN(pcm_serial_memory_read8(pcm,2,&phase));if (phase>0x4fu) phase=0;
        SYS_RUN(pcm_serial_memory_write8(pcm,2,phase));
        if (phase&15u) return PCM_FACTORY_WAIT_BOUNDARY;
        SYS_RUN(pcm_read8(pcm,0x3062,&port));uint8_t coils=port&0x0cu;
        port^=(coils==0 || coils==0x0c)?4u:8u;port|=0x30u;
        SYS_RUN(pcm_write8(pcm,0x3062,port));row=(uint16_t)(0xfbf2u+3u*(phase>>4));
    } else {
        SYS_RUN(pcm_read8(pcm,0x3062,&port));SYS_RUN(pcm_write8(pcm,0x3062,(uint8_t)(port&0xe3u)));
        SYS_RUN(pcm_write16(pcm,0x3fce,0));SYS_RUN(pcm_delay_cycles(pcm,11));
    }
    uint8_t pattern;SYS_RUN(pcm_read8(pcm,0x3060,&port));SYS_RUN(pcm_read8(pcm,row,&pattern));
    SYS_RUN(pcm_write8(pcm,0x3060,(uint8_t)((port&0x6fu)|pattern)));
    SYS_RUN(pcm_read8(pcm,0x3062,&port));SYS_RUN(pcm_read8(pcm,(uint16_t)(row+1u),&pattern));
    SYS_RUN(pcm_write8(pcm,0x3062,(uint8_t)((port&0xfcu)|pattern)));
    SYS_RUN(pcm_mask_irq(pcm,true));uint16_t control;SYS_RUN(pcm_read16(pcm,0x3ffc,&control));
    SYS_RUN(pcm_delay_cycles(pcm,11));SYS_RUN(pcm_read8(pcm,(uint16_t)(row+2u),&pattern));
    SYS_RUN(pcm_write16(pcm,0x3ffc,(uint16_t)((control&0xfff7u)|pattern)));
    SYS_RUN(pcm_delay_cycles(pcm,11));SYS_RUN(pcm_mask_irq(pcm,false));
    static const uint16_t addresses[]={0x3fd4,0x3fd6,0x3fd8,0x3fda,0x306a,0x306c,0x306e,0x3068};
    static const uint16_t enabled[]={0xd399,0xd366,0xd332,0xd2ff,0x7fb3,0x7fa6,0x7f66,0x0d73};
    for (unsigned i=0;i<8;++i) {
        SYS_RUN(pcm_write16(pcm,addresses[i],row==0xfc01?0xd000:enabled[i]));
        if (i<3) SYS_RUN(pcm_delay_cycles(pcm,11));
    }
    if (row!=0xfc01) SYS_RUN(pcm_serial_start(pcm,0xfbe0));
    return PCM_FACTORY_WAIT_BOUNDARY;
}
