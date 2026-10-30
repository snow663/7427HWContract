#include "scheduler.h"
/* Reference 7B1B, table word 7A93.
 * Stock body: 7B1B:C514;7B1E:F5DC;7B21:9E99;7B24:CA6B;7B27:ACA7
 * Body binding required unless state-only slot E. */
PcmStatus pcm_slot_07(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SLOT_07);
}
