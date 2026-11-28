#include "resident_input_private_1.h"

PcmStatus pcm_resident_fault_e60b(Pcm *pcm) { return paired_fault(pcm, 0x20, 4, 2); }
