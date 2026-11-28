#include "batch5.h"
#include "batch3.h"
#include "startup.h"
#include "service.h"
#include "system.h"
#include "../src/system/system_internal.h"

/* AE85..AEA3: connect the reconstructed eight-call prefix to the
 * existing F781/F64E service tail, with no intervening controller. */
PcmStatus closure_input_joined(Pcm *pcm)
{
    SYS_RUN(closure_input_prefix(pcm));
    return pcm_serial_service_poll(pcm);
}

/* 7100..711B on the host logical CPU, not native C's stack or CCR.
 * Incoming CCR is the externally established reset state. LDS/LDX/LDAA
 * clear N,Z,V on these nonzero nonnegative operands; C/H remain intact.
 * Do not simulate physical register time locks with guessed delays. */
PcmStatus closure_reset_prelude(Pcm *pcm,ClosureResetState *state)
{
    if(!pcm||!state) return PCM_BAD_CONFIGURATION;
    state->stack_pointer=0x03ff;
    state->register_base=0x1000;
    state->ccr&=(uint8_t)~0x0eu;
    state->next_pc=0x7108;
    SYS_RUN(pcm_write8(pcm,0x103d,3));
    state->register_base=0x3000;
    state->next_pc=0x710f;
    SYS_RUN(pcm_write8(pcm,0x3039,0xb8));
    state->next_pc=0x7113;
    SYS_RUN(pcm_write8(pcm,0x3024,3));
    state->next_pc=0x7115;
    SYS_RUN(pcm_update8(pcm,0x3038,0x20,0));
    state->next_pc=0x711a;
    SYS_RUN(pcm_write8(pcm,0x3035,0x1b));
    state->next_pc=0x711c;
    return PCM_OK;
}
PcmStatus closure_reset_task(Pcm *pcm,PcmTask task)
{
    if(task!=PCM_RESET_ENTRY) return PCM_BAD_CONFIGURATION;
    ClosureResetState state={.ccr=0xd0};
    return closure_reset_prelude(pcm,&state);
}

/* Host model joins existing resident boot components to the first
 * background pass. Caller must bind PCM_RESET_ENTRY to the logical
 * prelude, not to native execution. Factory admission skips the normal
 * controller initialization and rejoins at 7459. Actual reset/IRQ
 * interleaving and hardware response remain explicitly unverified. */
PcmStatus closure_reset_boot(Pcm *pcm,const PcmPlatform *platform,
                             const PcmCalibration *calibration)
{
    if(!platform||platform->task[PCM_RESET_ENTRY]!=closure_reset_task)
        return PCM_BAD_CONFIGURATION;
    PcmStatus status=pcm_reset_sequence(pcm,platform,calibration);
    if(status==PCM_FACTORY_BOUNDARY) {
        SYS_RUN(pcm_reset_timers(pcm));
    } else if(status!=PCM_OK) return status;
    return pcm_background_pass(pcm);
}
