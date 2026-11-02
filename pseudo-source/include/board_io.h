#ifndef PSEUDO_SOURCE_BOARD_IO_H
#define PSEUDO_SOURCE_BOARD_IO_H
#include "pcm.h"
PcmStatus pcm_board_latch(Pcm *);
PcmStatus pcm_board_ports(Pcm *);
PcmStatus pcm_map_input(Pcm *);
PcmStatus pcm_vss_sample(Pcm *);
PcmStatus pcm_brake_filter(Pcm *);
PcmStatus pcm_map_transient(Pcm *);
PcmStatus pcm_vss_calculate(Pcm *);
PcmStatus pcm_environment_inputs(Pcm *);
PcmStatus pcm_throttle_zero(Pcm *);
PcmStatus pcm_throttle_normalize(Pcm *, uint8_t *result);
PcmStatus pcm_coolant_input(Pcm *);
PcmStatus pcm_mat_input(Pcm *);
PcmStatus pcm_baro_input(Pcm *);
#endif
