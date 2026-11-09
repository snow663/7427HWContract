#ifndef PCM_SYSTEM_H
#define PCM_SYSTEM_H
#include "pcm.h"
/* Logical-address providers must bind RAM writes to their canonical owners. */
PcmStatus pcm_ram_clear(Pcm *,uint16_t address,uint16_t count);
PcmStatus pcm_factory_admit(Pcm *);
#endif
