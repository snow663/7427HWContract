#include "resident_input_private_1.h"

PcmStatus pcm_resident_fault_e6f5(Pcm *pcm) { return paired_fault(pcm, 2, 0x20, 4); }
