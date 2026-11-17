#include "system_internal.h"
/* FA5B..FBD6. The entry binding verifies target SP=03FF before this C frame;
 * no C helper resets a live stack. SWI and FBD4 stay explicit boundaries. */
PcmStatus pcm_factory_cycle(Pcm *pcm)
{
    SYS_RUN(pcm_run_task(pcm,PCM_FACTORY_ENTRY));
    SYS_RUN(pcm_adc_mux(pcm,1));SYS_RUN(pcm_adc_convert(pcm,1));
    uint8_t sample;SYS_RUN(pcm_read8(pcm,PCM_ADR1,&sample));
    if (sample>=100u || sample<40u) return PCM_TRAP_BOUNDARY;
    SYS_RUN(pcm_adc_convert(pcm,3));SYS_RUN(pcm_read8(pcm,PCM_ADR1,&sample));
    if (sample<=26u) return PCM_TRAP_BOUNDARY;
    SYS_RUN(pcm_mask_irq(pcm,false));SYS_RUN(pcm_watchdog_service(pcm));
    uint8_t id;SYS_RUN(pcm_serial_memory_read8(pcm,0x0364,&id));
    if (id!=2) {
        SYS_RUN(pcm_heartbeat_toggle(pcm));
        if (id!=3) goto upload_or_outputs;
        uint8_t flags;SYS_RUN(pcm_serial_memory_read8(pcm,1,&flags));
        if (!(flags&1u)) goto upload_or_outputs;
    }
    SYS_RUN(pcm_factory_call(pcm));return PCM_FACTORY_WAIT_BOUNDARY;
upload_or_outputs:
    if (id==1) { SYS_RUN(pcm_factory_upload(pcm));return PCM_FACTORY_WAIT_BOUNDARY; }
    return pcm_factory_outputs(pcm,id);
}
