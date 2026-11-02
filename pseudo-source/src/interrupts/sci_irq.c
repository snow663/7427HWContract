#include "serial.h"
#include "hardware.h"
#define RUN(call) do { PcmStatus result=(call);if (result!=PCM_OK) return result; } while (0)
/*FFD6->F7EA..F821. Target entry/RTI supplies the real frame and masked I state. */
PcmStatus pcm_sci_irq(Pcm *pcm)
{
    uint8_t control,status;RUN(pcm_read8(pcm,PCM_SCCR2,&control));
    if (control&0x20u) { RUN(pcm_read8(pcm,PCM_SCSR,&status));return (status&0x20u) ? pcm_serial_receive(pcm) : PCM_OK; }
    RUN(pcm_read8(pcm,PCM_SCCR2,&control));
    if (control&0x80u) { RUN(pcm_read8(pcm,PCM_SCSR,&status));return (status&0x80u) ? pcm_serial_transmit(pcm) : PCM_OK; }
    RUN(pcm_read8(pcm,PCM_SCCR2,&control));if (!(control&0x40u)) return PCM_OK;
    RUN(pcm_read8(pcm,PCM_SCSR,&status));if (!(status&0x40u)) return PCM_OK;
    RUN(pcm_write8(pcm,PCM_SCCR2,0x26));RUN(pcm_serial_driver(pcm,false));pcm->serial.busy=false;return PCM_OK;
}
