#include "system_internal.h"
/*74B4..74CF. The provider exposes the logical CPU stack region; native C
 * stack addresses/layout are not treated as the factory03B0..03FF window. */
PcmStatus pcm_stack_watermark(Pcm *pcm)
{
    uint16_t cursor=0x03b0;
    for (;;) {
        uint8_t value;SYS_RUN(pcm_read8(pcm,cursor,&value));
        if (value!=0 || cursor>=0x03ffu) break;
        ++cursor;
    }
    uint16_t previous;SYS_RUN(pcm_read16(pcm,0x02d1,&previous));
    if (previous!=0) {
        /* CPX rereads the word after LDD/BEQ; an interrupt can change it. */
        SYS_RUN(pcm_read16(pcm,0x02d1,&previous));
        if (cursor>=previous) return PCM_OK;
    }
    return pcm_write16(pcm,0x02d1,cursor);
}
