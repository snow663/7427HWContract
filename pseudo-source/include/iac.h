#ifndef PSEUDO_SOURCE_IAC_H
#define PSEUDO_SOURCE_IAC_H
#include "pcm.h"
PcmStatus pcm_iac_desired(Pcm *);
PcmStatus pcm_iac_kicker_disable(Pcm *);
PcmStatus pcm_iac_kicker_enable(Pcm *);
PcmStatus pcm_iac_movement(Pcm *);
PcmStatus pcm_iac_kicker(Pcm *);
PcmStatus pcm_iac_cold(Pcm *);
PcmStatus pcm_iac_transition_decay(Pcm *);
PcmStatus pcm_iac_transfer(Pcm *);
PcmStatus pcm_iac_publish(Pcm *, bool age_holds);
PcmStatus pcm_iac_background(Pcm *);
#endif
