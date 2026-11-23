#include "slot4_monitor.h"
/* ED3F DTC 81 solenoid pattern with a first-good recovery budget. */
PcmStatus pcm_diagnostic_solenoid_81(Pcm *pcm)
{
    return slot4_solenoid_monitor(pcm, 0x4, 0x20, 0x1, 0x17c, 0x5ba2, 0x2b);
}
