#include "control.h"
#include "hardware.h"
/* F5DC..F5E7: probe on every admission, independently of 0086.6. A matching
 * word calls the unsupplied 180C module; it is not a writable-memory test. */
PcmStatus pcm_connection_probe(Pcm *pcm)
{
    uint16_t signature;
    PcmStatus result = pcm_read16(pcm, PCM_EXTENSION_SIGNATURE, &signature);
    if (result != PCM_OK || signature != 0x7e18u) return result;
    return pcm_run_task(pcm, PCM_CONNECTION_EXTENSION);
}
