#ifndef PSEUDO_SOURCE_KNOCK_H
#define PSEUDO_SOURCE_KNOCK_H
#include "pcm.h"
PcmStatus pcm_knock_decay(Pcm *);
PcmStatus pcm_knock_sensor(Pcm *);
PcmStatus pcm_knock_retard(Pcm *);
PcmStatus pcm_knock_gains(Pcm *);
PcmStatus pcm_burst_gain(Pcm *);
PcmStatus pcm_knock_burst(Pcm *);
PcmStatus pcm_knock_corrections(Pcm *);
PcmStatus pcm_low_octane_learn(Pcm *);
PcmStatus pcm_low_octane_retard(Pcm *);
#endif
