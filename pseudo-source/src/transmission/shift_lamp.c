#include "control.h"
/* ACA7..ADA9: resident shift-lamp decision. Its source/body remains a named
 * dependency after slot7's complete CA6B producer. */
PcmStatus pcm_shift_lamp(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SHIFT_LAMP);
}
