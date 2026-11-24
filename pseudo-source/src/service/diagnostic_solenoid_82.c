#include "slot4_monitor.h"
/* ED80 DTC 82 solenoid pattern with a first-good recovery budget. */
PcmStatus pcm_diagnostic_solenoid_82(Pcm *pcm)
{
    return slot4_solenoid_monitor(pcm, 0x2, 0x10, 0x2, 0x17d, 0x5ba4, 0x2c);
}
