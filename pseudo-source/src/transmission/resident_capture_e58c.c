#include "resident_input_private_3.h"

/* E58C: unchanged-count exit returns the remaining timeout, NOT the
 * retained speed. The changed-count/zero-timeout path retains old speed. */
PcmStatus pcm_resident_capture_e58c(Pcm *pcm,uint16_t record,uint16_t gain,
                               uint8_t reload,uint16_t *result)
{
    uint8_t now,old,timeout;
    uint16_t capture,previous;
    SYS_RUN(pcm_read8(pcm,record+8u,&now));
    SYS_RUN(pcm_read8(pcm,record,&old));
    uint8_t delta=(uint8_t)(now-old);
    SYS_RUN(pcm_read8(pcm,record+3u,&timeout));
    if(!delta) {
        if(timeout) {
            --timeout;
            SYS_RUN(pcm_write8(pcm,record+3u,timeout));
            if(timeout) { *result=timeout; return PCM_OK; }
        }
        *result=0;
        return pcm_write16(pcm,record+4u,0);
    }
    if(timeout) {
        SYS_RUN(pcm_read16(pcm,record+6u,&capture));
        SYS_RUN(pcm_read16(pcm,record+1u,&previous));
        uint16_t speed=q(q((uint16_t)delta*8u,gain),(uint16_t)(capture-previous));
        SYS_RUN(pcm_write16(pcm,record+4u,speed));
    }
    SYS_RUN(pcm_read16(pcm,record+6u,&capture));
    SYS_RUN(pcm_write16(pcm,record+1u,capture));
    SYS_RUN(pcm_read8(pcm,record+8u,&now));
    SYS_RUN(pcm_write8(pcm,record,now));
    SYS_RUN(pcm_write8(pcm,record+3u,reload));
    return pcm_read16(pcm,record+4u,result);
}
