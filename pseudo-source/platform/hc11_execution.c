#include "hc11_execution.h"
#include "system.h"
#include "hardware.h"

void pcm_hc11_exec_reset(PcmHc11Execution *execution)
{
    pcm_hc11_c_entry_reset();
    if(execution==NULL)return;
    *execution=(PcmHc11Execution){0};
    execution->phase=PCM_HC11_EXEC_OFFLINE;
    execution->last_status=PCM_RESET_BOUNDARY;
}

static bool boot_claim_valid(Pcm *pcm,const PcmHc11BootWitness *proof)
{
    return pcm!=NULL && pcm->platform!=NULL &&
           pcm->calibration!=NULL &&
           pcm->calibration->format_version==1u &&
           pcm->platform->read8!=NULL &&
           pcm->platform->read16!=NULL &&
           pcm->platform->write8!=NULL &&
           pcm->platform->write16!=NULL &&
           pcm->platform->mask_irq!=NULL &&
           proof!=NULL && proof->reset_prelude_complete &&
           proof->irq_masked && proof->c_state_initialized &&
           proof->actuator_permissions_off &&
           proof->stack_pointer==0x03ffu &&
           proof->register_base==0x3000u;
}

PcmStatus pcm_hc11_exec_attach(PcmHc11Execution *execution,Pcm *pcm,
                                volatile uint8_t *mailbox,
                                const PcmHc11BootWitness *proof)
{
    if(execution==NULL)return PCM_BAD_CONFIGURATION;
    if(execution->phase!=PCM_HC11_EXEC_OFFLINE ||
       !boot_claim_valid(pcm,proof) || mailbox==NULL)
        return PCM_BAD_CONFIGURATION;
    pcm_hc11_c_entry_reset();
    PcmStatus result=pcm_hc11_c_entry_bind(pcm,mailbox,true);
    if(result!=PCM_OK) return result;
    execution->pcm=pcm;
    execution->mailbox=mailbox;
    execution->phase=PCM_HC11_EXEC_READY;
    execution->last_status=PCM_OK;
    return PCM_OK;
}

PcmStatus pcm_hc11_exec_background(PcmHc11Execution *execution)
{
    if(execution==NULL || execution->pcm==NULL ||
       execution->phase!=PCM_HC11_EXEC_READY)
        return PCM_BAD_CONFIGURATION;
    PcmStatus result=pcm_background_pass(execution->pcm);
    execution->last_status=result;
    if(result==PCM_BACKGROUND_WAIT_BOUNDARY) {
        ++execution->foreground_passes;
        execution->phase=PCM_HC11_EXEC_WAITING;
    } else if(result==PCM_STACK_RECOVERY_BOUNDARY) {
        execution->phase=PCM_HC11_EXEC_RECOVERY_REQUIRED;
    } else if(result!=PCM_OK) {
        execution->phase=PCM_HC11_EXEC_TRAPPED;
    }
    return result;
}

PcmStatus pcm_hc11_exec_interrupt(PcmHc11Execution *execution,
                                  uint16_t vector,
                                  const PcmHc11NativeFrame *frame,
                                  PcmHc11NativeAction *action)
{
    if(action==NULL)return PCM_BAD_CONFIGURATION;
    *action=PCM_HC11_NO_NATIVE_RETURN;
    if(execution==NULL || execution->pcm==NULL ||
       (execution->phase!=PCM_HC11_EXEC_WAITING &&
        execution->phase!=PCM_HC11_EXEC_READY))
        return PCM_BAD_CONFIGURATION;
    execution->last_vector=vector;
    PcmStatus result=pcm_hc11_vector_dispatch(execution->pcm,vector,frame,action);
    execution->last_status=result;
    if(result==PCM_OK && *action==PCM_HC11_NATIVE_RTI_REQUIRED) {
        ++execution->interrupt_returns;
        execution->phase=PCM_HC11_EXEC_READY;
    } else if(*action==PCM_HC11_NATIVE_STACK_RECOVERY) {
        execution->phase=PCM_HC11_EXEC_RECOVERY_REQUIRED;
    } else if(*action==PCM_HC11_NATIVE_RESET_REQUIRED) {
        /* A hardware reset restarts the MCU, not an in-place C jump. */
        pcm_hc11_exec_reset(execution);
    } else {
        execution->phase=PCM_HC11_EXEC_TRAPPED;
    }
    return result;
}
