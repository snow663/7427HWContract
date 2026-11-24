#include "control.h"
#include "hardware.h"
/* BMHM D5B7..D69E: final transmission proposed-gear arbitration.
 * Entry B is the unsigned proposed gear from preceding D4F7..D5A6.
 * This slice reproduces raw status gates, downshift wait, range limiter
 * E562, and selected-gear publication for the D4EB caller.
 * Each original BRSET/BRCLR/RMW is independently sampled to preserve
 * provider ordering and failure prefixes. No hardware coil command here. */
#define READ(a,v) do {PcmStatus s=pcm_read8(pcm,(a),&(v));if(s!=PCM_OK)return s;}while(0)
#define STORE(a,v) do {PcmStatus s=pcm_write8(pcm,(a),(v));if(s!=PCM_OK)return s;}while(0)
#define SET(a,m) do {PcmStatus s=pcm_update8(pcm,(a),0u,(m));if(s!=PCM_OK)return s;}while(0)
#define CLEAR(a,m) do {PcmStatus s=pcm_update8(pcm,(a),(m),0u);if(s!=PCM_OK)return s;}while(0)
PcmStatus pcm_transmission_gear_finalize(Pcm *pcm, uint8_t proposed)
{
    if(pcm==NULL)return PCM_BAD_CONFIGURATION;
    uint8_t flags,gear,observed,limit;
    READ(0x0099u,flags);
    if(flags&0x08u)proposed=1u; /* D5B7 */

    READ(0x0099u,flags);
    if(flags&0x01u) { /* D5BD..D5D3; repeated D9 compares are real */
        READ(0x00d9u,gear); /* D5C1 */
        if(proposed>gear) {
            if(proposed>1u) {
                READ(0x00d9u,gear); /* D5D3 branch */
                proposed=gear;
            }
        } else {
            READ(0x00d9u,gear); /* D5CB: required second memory sample */
            if(proposed<gear && proposed<1u) {
                READ(0x00d9u,gear); /* D5D3 */
                proposed=gear;
            }
        }
    }
    READ(0x0099u,flags);
    if((flags&0x01u) && proposed==1u) {
        READ(0x00d7u,observed);
        READ(0x5d39u,limit);
        if(observed>=limit)proposed=3u;
    }

    READ(0x0098u,flags);
    if(flags&0x08u)proposed=1u;
    else {
        READ(0x0099u,flags);
        if(flags&0x02u)proposed=1u;
    }

    CLEAR(0x0083u,0x24u);
    READ(0x00d9u,gear);
    if(proposed>gear)SET(0x0083u,0x04u);
    else if(proposed<gear)SET(0x0083u,0x20u);

    READ(0x0083u,flags);
    if(flags&0x20u) {
        READ(0x00d9u,observed);
        if(observed==2u) {
            READ(0x0083u,flags);
            if(!(flags&0x40u)) {
                SET(0x0083u,0x40u);
                CLEAR(0x0083u,0x80u);
            }
            goto decision;
        }
    }
    CLEAR(0x0083u,0x40u);
    READ(0x0135u,observed);
    observed++;
    if(observed!=0u)STORE(0x0135u,observed);

decision:
    READ(0x0083u,flags);
    if(!(flags&0x04u)) {
        READ(0x0083u,flags);
        if(flags&0x20u) {
            READ(0x00d9u,gear);
            if(gear==3u)STORE(0x0135u,0u);
            READ(0x0083u,flags);
            if(flags&0x40u) {
                READ(0x0135u,observed);
                READ(0x5d32u,limit);
                if(observed>limit) {
                    READ(0x5d33u,limit);
                    if(observed<limit) {
                        READ(0x0118u,observed);
                        if(observed==0u) {
                            READ(0x0134u,observed);
                            READ(0x5d31u,limit);
                            if(observed<limit) {
                                goto retain;
                            }
                        }
                    }
                }
            }
            READ(0x0125u,observed);
            READ(0x5d30u,limit);
            if(observed<limit)goto retain;
        }
    }
    goto output;
retain:
    READ(0x00d9u,proposed); /* D65A samples the live gear after the delay tests. */
output:
    CLEAR(0x0085u,0x20u);
    READ(0x00a2u,flags);
    if(flags&0x04u) {
        if(proposed==3u) {
            READ(0x0197u,observed);
            if(observed!=0u)SET(0x0085u,0x20u);
        }
    }
    uint8_t capped;
    PcmStatus status=pcm_transmission_gear_limit(pcm,proposed,&capped);
    if(status!=PCM_OK)return status;
    CLEAR(0x0083u,0x09u);
    READ(0x0103u,observed);
    if(observed!=0u) {
        observed--;
        if(observed>3u) {
            STORE(0x0103u,4u);
            pcm->transmission.service_gear=4u;
            observed=3u;
        }
        STORE(0x0187u,255u);
        capped=observed;
    } else {
        READ(0x00d9u,gear);
        if(capped==gear) {
            pcm->transmission.selected_gear=gear;
            return PCM_OK;
        }
        if(capped<gear)SET(0x0083u,0x08u);
        else SET(0x0083u,0x01u);
    }
    STORE(0x00d9u,capped);
    pcm->transmission.selected_gear=capped; /* C514 consumes the committed D9. */
    return PCM_OK;
}
