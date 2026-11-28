#include "resident_input_private_2.h"
static const Diagnostic range_pattern={0x5b01,0x17,0x94,0x165,0x5b51,0x22,0x5b52,2,8};

PcmStatus pcm_resident_diag_e8c8(Pcm *pcm) { return pattern_monitor(pcm,&range_pattern,0xa2,0x80); }
