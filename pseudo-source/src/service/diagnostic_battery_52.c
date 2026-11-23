#include "slot4_monitor.h"
/* EA40 DTC 52 battery high comparison with a word timer. */
PcmStatus pcm_diagnostic_battery_52(Pcm *pcm)
{
    return slot4_battery_monitor(pcm, true);
}
