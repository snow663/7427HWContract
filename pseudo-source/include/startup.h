#ifndef PSEUDO_SOURCE_STARTUP_H
#define PSEUDO_SOURCE_STARTUP_H
#include "hardware.h"
PcmStatus pcm_reset_entry(Pcm *);
PcmStatus pcm_reset_cpu(Pcm *);
PcmStatus pcm_reset_outputs(Pcm *);
PcmStatus pcm_reset_ram(Pcm *);
PcmStatus pcm_reset_sensors(Pcm *);
PcmStatus pcm_reset_retained(Pcm *);
PcmStatus pcm_reset_controllers(Pcm *);
PcmStatus pcm_reset_serial(Pcm *);
#endif
