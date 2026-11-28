#ifndef PCM_SERVICE_H
#define PCM_SERVICE_H
#include "pcm.h"
/* Logical-address accesses share serial.h's canonical-owner/provider contract. */
PcmStatus pcm_diagnostic_slot_d(Pcm *);
PcmStatus pcm_diagnostic_engine_inputs(Pcm *);
PcmStatus pcm_diagnostic_egr_test(Pcm *);
PcmStatus pcm_diagnostic_engine_feedback(Pcm *);
PcmStatus pcm_diagnostic_report(Pcm *);
PcmStatus pcm_diagnostic_flash_codes(Pcm *);
PcmStatus pcm_diagnostic_checksum(Pcm *,uint8_t *);
PcmStatus pcm_diagnostic_clear_engine(Pcm *);
PcmStatus pcm_diagnostic_clear_transmission(Pcm *);
PcmStatus pcm_service_status(Pcm *);
PcmStatus pcm_service_transmission(Pcm *);
PcmStatus pcm_service_engine(Pcm *);
PcmStatus pcm_service_clear(Pcm *);
PcmStatus pcm_service_cleanup(Pcm *);
PcmStatus pcm_serial_service(Pcm *);
PcmStatus pcm_serial_service_poll(Pcm *);
/* AE85..AE9C: resident prefix available with explicit research opt-in. */
PcmStatus pcm_transmission_input_prefix(Pcm *);
#endif
