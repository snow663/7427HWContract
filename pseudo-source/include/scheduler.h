#ifndef PSEUDO_SOURCE_SCHEDULER_H
#define PSEUDO_SOURCE_SCHEDULER_H
#include "pcm.h"
PcmStatus pcm_phase_advance(Pcm *);
PcmStatus pcm_dispatch_fast(Pcm *);
PcmStatus pcm_dispatch_slot(Pcm *);
PcmStatus pcm_main_pass(Pcm *);
PcmStatus pcm_dispatcher(Pcm *);
PcmStatus pcm_fast_service(Pcm *);
PcmStatus pcm_profile_tail(Pcm *);
PcmStatus pcm_periodic_irq(Pcm *);
PcmStatus pcm_slot_00(Pcm *); PcmStatus pcm_slot_01(Pcm *);
PcmStatus pcm_slot_02(Pcm *); PcmStatus pcm_slot_03(Pcm *);
PcmStatus pcm_slot_04(Pcm *); PcmStatus pcm_slot_05(Pcm *);
PcmStatus pcm_slot_06(Pcm *); PcmStatus pcm_slot_07(Pcm *);
PcmStatus pcm_slot_08(Pcm *); PcmStatus pcm_slot_09(Pcm *);
PcmStatus pcm_slot_0a(Pcm *); PcmStatus pcm_slot_0b(Pcm *);
PcmStatus pcm_slot_0c(Pcm *); PcmStatus pcm_slot_0d(Pcm *);
PcmStatus pcm_slot_0e(Pcm *); PcmStatus pcm_slot_0f(Pcm *);
#endif
