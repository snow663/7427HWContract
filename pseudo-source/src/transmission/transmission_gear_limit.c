#include "control.h"
/* BMHM $E562..$E57B. The stock entry consumes the proposed gear in A,
 * extracts $(00A2 & 7) >> 1 with zero remapped to six before shift,
 * and reads ROM[E57C + 4*range + proposed]. The table address is not
 * range-clamped: preserve the CPU's 16-bit pointer arithmetic for all
 * 256 possible A inputs, even when it indexes adjacent ROM bytes.
 * The returned A is the unsigned minimum of the source byte and input.
 * No transmission or hardware state is published by this helper. */
PcmStatus pcm_transmission_gear_limit(Pcm *pcm, uint8_t proposed, uint8_t *capped)
{
    if (pcm == NULL || capped == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t state, bound;
    PcmStatus status=pcm_read8(pcm,0x00a2u,&state);
    if (status != PCM_OK) return status;
    uint8_t bin=(uint8_t)(state & 7u);
    if(bin==0u)bin=6u;
    bin>>=1;
    uint16_t address=(uint16_t)(0xe57cu+4u*(unsigned)bin+(unsigned)proposed);
    status=pcm_read8(pcm,address,&bound);
    if(status!=PCM_OK)return status;
    *capped=bound<=proposed?bound:proposed;
    return PCM_OK;
}
