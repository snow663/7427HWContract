#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*F280..F28D. Reset all21 retained cells, not just the selected one. */
PcmStatus pcm_blm_reset(Pcm *pcm)
{
    for (unsigned i=0;i<21;++i) pcm->fuel.blm_cells[i] = 128;
    return PCM_OK;
}
