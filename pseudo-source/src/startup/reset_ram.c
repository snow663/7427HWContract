#include "startup.h"
#include "system.h"
#include "serial.h"
#define RUN(call) do { PcmStatus result=(call);if (result!=PCM_OK) return result; } while (0)
/*7164..7189. Keep the three working-RAM calls before the byte serial clear.
 * The address-space provider commits each word to its existing named owners. */
PcmStatus pcm_reset_ram(Pcm *pcm)
{
    RUN(pcm_ram_clear(pcm,0x0036,0x00ca));
    RUN(pcm_ram_clear(pcm,0x0100,0x019d));
    RUN(pcm_ram_clear(pcm,0x0800,0x0100));
    return pcm_serial_clear_ram(pcm);
}
