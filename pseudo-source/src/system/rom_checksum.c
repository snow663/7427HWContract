#include "system_internal.h"
/*F2AA..F2FC for its rooted caller X=4008 only. The first COP pair follows
 *255 eight-byte groups; later pairs follow256. The order here is55 thenAA. */
PcmStatus pcm_rom_checksum(Pcm *pcm,uint16_t *out)
{
    if (out==NULL) return PCM_BAD_CONFIGURATION;
    uint16_t address=0x4008,sum=0;unsigned groups=255;
    do {
        for (unsigned group=0;group<groups;++group) {
            for (unsigned offset=0;offset<8;++offset) {
                uint8_t value;SYS_RUN(pcm_read8(pcm,(uint16_t)(address+offset),&value));
                sum=(uint16_t)(sum+value);
            }
            address=(uint16_t)(address+8u);
        }
        SYS_RUN(pcm_write8(pcm,PCM_COPRST,0x55));
        SYS_RUN(pcm_write8(pcm,PCM_COPRST,0xaa));
        groups=256;
    } while (address!=0);
    *out=sum;return PCM_OK;
}
