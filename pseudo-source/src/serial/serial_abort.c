#include "serial_internal.h"
/*FA4D..FA5A. Preserve session bits, accepted ID and prior payload stores. */
PcmStatus pcm_serial_abort(Pcm *pcm)
{
    pcm->serial.descriptor=0;pcm->serial.count=0;pcm->serial.checksum=0;
    return pcm_write8(pcm,PCM_SCCR2,0x26);
}
