#include "resident_input_private_3.h"

/* F420 uses BLT (N xor V) after subtraction: compare the signed
 * operands, unlike F436 which uses unsigned borrow. Reread the coefficient as in ROM. */
PcmStatus pcm_resident_lag_f420(Pcm *pcm,uint16_t target,uint16_t old,
                            uint16_t coefficient,uint16_t *result)
{
    uint16_t delta=(uint16_t)(target-old);
    uint8_t gain;
    SYS_RUN(pcm_read8(pcm,coefficient,&gain));
    uint16_t part=(uint16_t)(old+(delta>>8)*gain);
    if((target^0x8000u)<(old^0x8000u)) {
        SYS_RUN(pcm_read8(pcm,coefficient,&gain));
        part=(uint16_t)(part-(uint16_t)gain*256u);
    }
    SYS_RUN(pcm_read8(pcm,coefficient,&gain));
    *result=(uint16_t)(part+(((delta&255u)*gain+128u)>>8));
    return PCM_OK;
}
