#ifndef PCM_INTERRUPTS_H
#define PCM_INTERRUPTS_H
#include "pcm.h"
/* Resident leaf bodies only. Hardware entry/frame/RTI and actual reset/halt
 * transfers belong to target assembly. The XIRQ frame address is supplied by
 * that entry shim, never inferred from a native C stack pointer. */
PcmStatus pcm_swi_irq(Pcm *);
PcmStatus pcm_illegal_trap(Pcm *);
PcmStatus pcm_cop_reset(Pcm *);
PcmStatus pcm_clock_failure(Pcm *);
PcmStatus pcm_external_reset(Pcm *);
PcmStatus pcm_xirq_irq(Pcm *,uint16_t saved_ccr_address);
PcmStatus pcm_factory_reference_irq(Pcm *);
PcmStatus pcm_timer_fallback_irq(Pcm *);
PcmStatus pcm_overflow_fallback_irq(Pcm *);
PcmStatus pcm_spi_irq(Pcm *);
#endif
