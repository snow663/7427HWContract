#ifndef PCM_FUEL_RAM_OWNERS_H
#define PCM_FUEL_RAM_OWNERS_H
#include "pcm.h"
/* Source-address adapter for the $7D4B prefix. It is a *partial* map:
 * false means the caller must use its real provider. For shared flag
 * bytes, residual supplies the unowned bits; write callers must retain
 * those raw bits in their backing provider. No 64 KB production mirror. */
bool pcm_fuel_ram_owner_read8(const Pcm *,uint16_t address,uint8_t residual,uint8_t *out);
bool pcm_fuel_ram_owner_write8(Pcm *,uint16_t address,uint8_t value);
bool pcm_fuel_ram_owner_read16(const Pcm *,uint16_t address,uint16_t *out);
bool pcm_fuel_ram_owner_write16(Pcm *,uint16_t address,uint16_t value);
#endif
