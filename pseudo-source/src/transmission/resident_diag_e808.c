#include "resident_input_private_2.h"
static const Diagnostic low_tps={0x5b01,0x17,0x94,0x163,0x5b20,0x20,0x5b21,0x80,2};

PcmStatus pcm_resident_diag_e808(Pcm *pcm) { return tps_monitor(pcm,&low_tps,0x5b1f,false); }
