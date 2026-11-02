#ifndef PSEUDO_SOURCE_FUEL_H
#define PSEUDO_SOURCE_FUEL_H
#include "pcm.h"
PcmStatus pcm_fuel_finalize(Pcm *);
PcmStatus pcm_fuel_publish(Pcm *, uint16_t pulse);
PcmStatus pcm_injector_offset(Pcm *);
PcmStatus pcm_fuel_battery_state(Pcm *);
PcmStatus pcm_fuel_throttle(Pcm *);
PcmStatus pcm_fuel_density(Pcm *);
PcmStatus pcm_fuel_charge_temperature(Pcm *);
PcmStatus pcm_fuel_ve(Pcm *);
PcmStatus pcm_fuel_base_publish(Pcm *);
PcmStatus pcm_fuel_air_charge(Pcm *);
#endif
