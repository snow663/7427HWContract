#include "system_internal.h"
/*746C..74B2. Resident cursor progression is0000..0400, then0800..0900,
 * in16-byte blocks. A block is masked; the whole pass is not atomic. */
PcmStatus pcm_ram_refresh(Pcm *pcm)
{
    uint8_t flags;SYS_RUN(pcm_read8(pcm,0x0051,&flags));
    if (!(flags&4u)) return PCM_OK;
    uint16_t cursor;SYS_RUN(pcm_read16(pcm,0x029b,&cursor));
    for (;;) {
        if (cursor==0x0400u) {
            cursor=0x0800;SYS_RUN(pcm_write16(pcm,0x029b,cursor));
        }
        if (cursor==0x0900u) break;
        SYS_RUN(pcm_mask_irq(pcm,true));
        for (unsigned offset=0;offset<16;offset+=2) {
            uint16_t value,address=(uint16_t)(cursor+offset);
            SYS_RUN(pcm_read16(pcm,address,&value));SYS_RUN(pcm_write16(pcm,address,value));
        }
        cursor=(uint16_t)(cursor+16u);SYS_RUN(pcm_write16(pcm,0x029b,cursor));
        SYS_RUN(pcm_mask_irq(pcm,false));
    }
    /* Literal CLR029B, not a word clear: retain a separately changed low byte. */
    SYS_RUN(pcm_write8(pcm,0x029b,0));
    return sys_update(pcm,0x0051,4,0);
}
