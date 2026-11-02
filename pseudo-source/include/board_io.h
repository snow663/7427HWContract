#ifndef PSEUDO_SOURCE_BOARD_IO_H
#define PSEUDO_SOURCE_BOARD_IO_H
#include "pcm.h"
PcmStatus pcm_board_latch(Pcm *);
PcmStatus pcm_board_ports(Pcm *);
PcmStatus pcm_map_input(Pcm *);
PcmStatus pcm_vss_sample(Pcm *);
PcmStatus pcm_brake_filter(Pcm *);
#endif
