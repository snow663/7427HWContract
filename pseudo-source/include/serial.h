#ifndef PCM_SERIAL_H
#define PCM_SERIAL_H
#include "pcm.h"
/* Logical-address access: owned serial RAM is native; the platform supplies
 * coherent bindings for all other RAM/ROM/device addresses. */
PcmStatus pcm_serial_memory_read8(Pcm *,uint16_t,uint8_t *);
PcmStatus pcm_serial_memory_read16(Pcm *,uint16_t,uint16_t *);
PcmStatus pcm_serial_memory_write8(Pcm *,uint16_t,uint8_t);
PcmStatus pcm_serial_clear_ram(Pcm *);
PcmStatus pcm_serial_find(Pcm *,uint8_t,uint16_t *);
/* RX payload caller supplies a captured descriptor and ordinal < length. */
PcmStatus pcm_serial_payload(Pcm *,uint16_t,uint8_t,uint8_t);
PcmStatus pcm_serial_accept(Pcm *,uint16_t);
PcmStatus pcm_serial_abort(Pcm *);
/* Caller retains the source IRQ-mask precondition around this word RMW. */
PcmStatus pcm_serial_driver(Pcm *,bool);
PcmStatus pcm_serial_start(Pcm *,uint16_t);
PcmStatus pcm_serial_send(Pcm *,uint8_t);
PcmStatus pcm_serial_finish(Pcm *);
/* TX caller has already handled header/echo/checksum/completion priority. */
PcmStatus pcm_serial_next(Pcm *,uint16_t,uint8_t,uint8_t *);
PcmStatus pcm_serial_receive(Pcm *);
PcmStatus pcm_serial_transmit(Pcm *);
PcmStatus pcm_serial_idle(Pcm *);
#endif
