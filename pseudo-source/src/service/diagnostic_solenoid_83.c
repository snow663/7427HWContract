#include "slot4_monitor.h"
/* EDC1 DTC 83 solenoid pattern with a first-good recovery budget. */
PcmStatus pcm_diagnostic_solenoid_83(Pcm *pcm)
{
    return slot4_solenoid_monitor(pcm, 0x1, 0x30, 0x4, 0x17e, 0x5ba6, 0x2d);
}
