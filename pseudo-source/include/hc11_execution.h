#ifndef PCM_HC11_EXECUTION_H
#define PCM_HC11_EXECUTION_H

#include "hc11_irq_mailbox.h"

/* Simulator/native integration port. This executes the EXISTING C
 * pseudo-source and reports CPU transfer requirements. No C routine
 * pretends to perform the HC11's WAI, RTI, LDS, SWI, STOP or vector fetch. */
typedef enum {
    PCM_HC11_EXEC_OFFLINE,
    PCM_HC11_EXEC_READY,
    PCM_HC11_EXEC_WAITING,
    PCM_HC11_EXEC_RECOVERY_REQUIRED,
    PCM_HC11_EXEC_TRAPPED
} PcmHc11ExecutionPhase;

typedef struct {
    /* Assertions supplied by a traced ROM reset in the simulator or a
     * separately verified native assembly prelude, never by host guesses. */
    uint16_t stack_pointer;     /* $03FF immediately after stock LDS */
    uint16_t register_base;     /* $3000 following INIT03 */
    bool reset_prelude_complete;
    bool irq_masked;
    bool c_state_initialized;
    bool actuator_permissions_off;
} PcmHc11BootWitness;

typedef struct {
    Pcm *pcm;
    volatile uint8_t *mailbox;
    PcmHc11ExecutionPhase phase;
    PcmStatus last_status;
    uint16_t last_vector;
    unsigned foreground_passes;
    unsigned interrupt_returns;
} PcmHc11Execution;

/* Attach ONLY after a native boot has executed and target calibration and
 * Pcm field state have been initialized. Does not run a fake C reset or
 * double-apply the factory $7100 processor/board initialization.
 * Does not enable any interrupt vector or actuator. */
PcmStatus pcm_hc11_exec_attach(PcmHc11Execution *execution,Pcm *pcm,
                                volatile uint8_t *mailbox,
                                const PcmHc11BootWitness *proof);

/* Run one stock background pass. PCM_BACKGROUND_WAIT_BOUNDARY requests a
 * target WAI/interrupt-frame wait, never a successful C return from WAI. */
PcmStatus pcm_hc11_exec_background(PcmHc11Execution *execution);

/* Execute a previously hardware-admitted interrupt's existing resident C
 * routine, returning its required native transfer action to the caller.
 * The simulator must stack CPU registers/restore RTI itself. A real
 * HC11 ROM must run through its separately verified assembly gateway. */
PcmStatus pcm_hc11_exec_interrupt(PcmHc11Execution *execution,
                                  uint16_t vector,
                                  const PcmHc11NativeFrame *frame,
                                  PcmHc11NativeAction *native_action);

/* Simulator/hardware reset admission never continues a stale C call frame. */
void pcm_hc11_exec_reset(PcmHc11Execution *execution);
#endif
