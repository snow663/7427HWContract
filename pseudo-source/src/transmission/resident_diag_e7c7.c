#include "resident_input_private_2.h"
static const Diagnostic high_tps={0x5b00,0x16,0x94,0x162,0x5b1d,0x1f,0x5b1e,1,1};

PcmStatus pcm_resident_diag_e7c7(Pcm *pcm) { return tps_monitor(pcm,&high_tps,0x5b1c,true); }
