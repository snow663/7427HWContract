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
PcmStatus pcm_iac_follower(Pcm *);
PcmStatus pcm_iac_slow_decays(Pcm *);
PcmStatus pcm_iac_drive_limit(Pcm *);
PcmStatus pcm_iac_kicker_diagnostic(Pcm *);
PcmStatus pcm_iac_learning_diagnostic(Pcm *);
PcmStatus pcm_iac_reset_admit(Pcm *);
PcmStatus pcm_iac_reset_request(Pcm *);
PcmStatus pcm_iac_slow(Pcm *);
PcmStatus pcm_iac_service(Pcm *, bool *exited);
PcmStatus pcm_iac_seed_cells(Pcm *);
PcmStatus pcm_iac_start(Pcm *);
PcmStatus pcm_iac_context(Pcm *);
PcmStatus pcm_iac_error(Pcm *);
PcmStatus pcm_iac_integral(Pcm *);
PcmStatus pcm_iac_proportional(Pcm *);
PcmStatus pcm_iac_derivative(Pcm *);
PcmStatus pcm_iac_compose(Pcm *);
PcmStatus pcm_iac_convert(Pcm *, uint16_t flow);
#endif
