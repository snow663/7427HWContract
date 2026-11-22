#include "control.h"
/* BMHM $D8CE..$D8EF conditional ROM pointer-table selection.
 * Input X is the table and B is the caller's gear slot. The helper
 * checks $0098.2 then ($00A2&7); a zero flag/zero pointer returns
 * accumulator A=0 with carry SET (represented by valid=false).
 * On success X is a big-endian ROM word and the pointed byte is A.
 * Exactly stock 8-bit ASLA/TAB displacement wrap applies BEFORE ABX.
 * No physical shift output or memory publication occurs. */
PcmStatus pcm_transmission_threshold_select(Pcm *pcm, uint16_t table,
                                            uint8_t slot, uint8_t *value,
                                            bool *valid)
{
    if(pcm==NULL || value==NULL || valid==NULL)return PCM_BAD_CONFIGURATION;
    uint8_t flags,range;
    PcmStatus status=pcm_read8(pcm,0x0098u,&flags);
    if(status!=PCM_OK)return status;
    if(flags&0x04u) {
        *value=0u;*valid=false;
        return PCM_OK;
    }
    status=pcm_read8(pcm,0x00a2u,&range);
    if(status!=PCM_OK)return status;
    range&=7u;
    if(range==0u) {
        *value=0u;*valid=false;
        return PCM_OK;
    }
    uint8_t displacement=(uint8_t)(2u*(uint8_t)(slot+3u*(range>>1)));
    uint16_t pointer=0u;
    status=pcm_read16(pcm,(uint16_t)(table+displacement),&pointer);
    if(status!=PCM_OK)return status;
    if(pointer==0u) {
        *value=0u;*valid=false;
        return PCM_OK;
    }
    uint8_t threshold;
    status=pcm_read8(pcm,pointer,&threshold);
    if(status!=PCM_OK)return status;
    *value=threshold;*valid=true;
    return PCM_OK;
}
