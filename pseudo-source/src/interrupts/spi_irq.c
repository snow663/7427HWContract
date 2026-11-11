#include "interrupts.h"
/*FFD8 ->FC44 is only RTI. It does not read status/data or acknowledge SPI. */
PcmStatus pcm_spi_irq(Pcm *pcm)
{
    (void)pcm;return PCM_OK;
}
