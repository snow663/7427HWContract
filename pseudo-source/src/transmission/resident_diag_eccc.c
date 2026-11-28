#include "resident_input_private_2.h"
static const Diagnostic request_pattern={0x5b07,0x1d,0x95,0x179,0x5b9d,0,0,0x20,0x40};

PcmStatus pcm_resident_diag_eccc(Pcm *pcm) { return pattern_monitor(pcm,&request_pattern,0x9f,8); }
