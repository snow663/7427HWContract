#ifndef PSEUDO_SOURCE_FUEL_H
#define PSEUDO_SOURCE_FUEL_H
#include "pcm.h"
PcmStatus pcm_fuel_finalize(Pcm *);
PcmStatus pcm_fuel_publish(Pcm *, uint16_t pulse);
PcmStatus pcm_injector_offset(Pcm *);
PcmStatus pcm_fuel_battery_state(Pcm *);
#endif
