#include "iac.h"
#include "../system/system_internal.h"
/* 925E..92A3. Existing cell seeding and kicker cleanup keep their native owners. */
PcmStatus pcm_iac_boot(Pcm *pcm)
{
    uint8_t value,flags;SYS_RUN(pcm_read8(pcm,0x4ef2,&value));
    SYS_RUN(pcm_write8(pcm,0x0885,(uint8_t)(value*4u)));
    SYS_RUN(pcm_read8(pcm,0x46,&flags));
    if (flags&0x40u) {
        SYS_RUN(pcm_read8(pcm,0x4eb0,&value));SYS_RUN(pcm_write8(pcm,7,value));
        SYS_RUN(pcm_iac_seed_cells(pcm));
    }
    SYS_RUN(pcm_read8(pcm,4,&flags));
    if (flags&8u) SYS_RUN(pcm_iac_step_disable(pcm));
    else SYS_RUN(pcm_iac_restore(pcm));
    SYS_RUN(pcm_read8(pcm,0x4e8f,&flags));
    if (flags&4u) {
        uint8_t baro,limit;SYS_RUN(pcm_read8(pcm,0x02f4,&baro));SYS_RUN(pcm_read8(pcm,0x50ce,&limit));
        bool enable=baro<=limit;
        if (!enable) {
            uint8_t coolant;SYS_RUN(pcm_read8(pcm,6,&coolant));SYS_RUN(pcm_read8(pcm,0x50c7,&limit));
            enable=coolant<limit;
        }
        if (enable) SYS_RUN(sys_update(pcm,0x37,0,4));
        else SYS_RUN(pcm_iac_kicker_disable(pcm));
    }
    SYS_RUN(pcm_read8(pcm,7,&value));SYS_RUN(pcm_write8(pcm,8,value));
    return sys_update(pcm,0x4c,0,0x10);
}
