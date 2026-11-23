#include "slot4_monitor.h"
/* EA7C DTC 53 battery high comparison with a byte timer. */
PcmStatus pcm_diagnostic_battery_53(Pcm *pcm)
{
    return slot4_battery_monitor(pcm, false);
}
