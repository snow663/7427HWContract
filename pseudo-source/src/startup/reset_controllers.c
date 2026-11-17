#include "startup.h"
#include "board_io.h"
#include "control.h"
#include "iac.h"
#include "spark.h"
#include "../system/system_internal.h"
/* 7393..7430. Only source-specified high bytes are seeded; retained fractions
 * and the pre-conversion coolant sample survive across their actual uses. */
PcmStatus pcm_reset_controllers(Pcm *pcm)
{
    uint8_t raw,value,previous,coolant,threshold;uint16_t word;
    SYS_RUN(pcm_read8(pcm,0x082e,&raw));SYS_RUN(pcm_write8(pcm,0x01c6,raw));
    SYS_RUN(pcm_write8(pcm,0x01c3,raw));
    unsigned map=(unsigned)(uint8_t)(raw-26u)*151u+64u;map=map*2u;
    value=map>65535u?255:(uint8_t)(map>>8);
    SYS_RUN(pcm_write8(pcm,0x01c0,value));SYS_RUN(pcm_write8(pcm,0x01c7,value));
    SYS_RUN(pcm_baro_seed(pcm));SYS_RUN(sys_update(pcm,0x4e,0,1));
    SYS_RUN(sys_update(pcm,0x43,0,0x80));SYS_RUN(sys_update(pcm,4,0x10,0));
    SYS_RUN(pcm_read8(pcm,6,&previous));SYS_RUN(pcm_coolant_input(pcm));
    SYS_RUN(pcm_environment_inputs(pcm));SYS_RUN(pcm_spark_auxiliary(pcm));
    SYS_RUN(pcm_read8(pcm,6,&coolant));SYS_RUN(pcm_write8(pcm,0x0282,coolant));
    SYS_RUN(pcm_read8(pcm,0x495a,&threshold));
    if (previous>=threshold) {
        SYS_RUN(pcm_read8(pcm,0x495b,&threshold));
        if (coolant>=threshold) SYS_RUN(sys_update(pcm,4,0,0x10));
    }
    SYS_RUN(pcm_iac_boot(pcm));SYS_RUN(pcm_read8(pcm,0x48be,&value));
    SYS_RUN(pcm_write8(pcm,0x01d5,value));SYS_RUN(pcm_write8(pcm,0x01d0,value));
    SYS_RUN(pcm_write8(pcm,0x01d2,value));SYS_RUN(pcm_throttle_zero(pcm));
    SYS_RUN(pcm_transmission_throttle(pcm));SYS_RUN(pcm_read8(pcm,0x01d9,&value));
    SYS_RUN(pcm_write8(pcm,0x01dc,value));SYS_RUN(pcm_write8(pcm,0x01da,value));
    SYS_RUN(pcm_write8(pcm,0x01db,value));SYS_RUN(pcm_write8(pcm,0x01de,value));
    SYS_RUN(pcm_read8(pcm,0x48a5,&value));SYS_RUN(pcm_write8(pcm,0x01b5,value));
    SYS_RUN(pcm_egr_feedback(pcm));SYS_RUN(pcm_read8(pcm,0x01a1,&value));
    SYS_RUN(pcm_write16(pcm,0x01a2,(uint16_t)((uint16_t)value*256u)));
    SYS_RUN(pcm_controller_baselines(pcm));SYS_RUN(pcm_read8(pcm,0x00a8,&value));
    SYS_RUN(pcm_read8(pcm,0x4071,&threshold));
    uint8_t converter=0;if (value>=threshold) SYS_RUN(pcm_read8(pcm,0x4072,&converter));
    SYS_RUN(pcm_write8(pcm,0x78,converter));SYS_RUN(pcm_read16(pcm,0x3fca,&word));
    SYS_RUN(pcm_write16(pcm,0x0205,word));SYS_RUN(pcm_read16(pcm,0x3012,&word));
    SYS_RUN(pcm_write16(pcm,0x0851,word));SYS_RUN(pcm_read8(pcm,0x48e7,&value));
    return pcm_write8(pcm,0x024a,value);
}
