#include "scheduler.h"
#include "hardware.h"
/*7AA6..7AAC: battery acquisition followed by the literal CF15 RTS. */
PcmStatus pcm_slot_00(Pcm *pcm)
{
    return pcm_battery_input(pcm);
}
