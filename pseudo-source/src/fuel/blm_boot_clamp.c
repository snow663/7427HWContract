#include "fuel.h"
#include "feedback_internal.h"
#include "hardware.h"
/*F28E..F2A9. Boot bounds differ from runtime validity/learning bounds. */
PcmStatus pcm_blm_boot_clamp(Pcm *pcm)
{
    FB_CAL();
    for (unsigned i=0;i<21;++i) {
        if (pcm->fuel.blm_cells[i] > cal->boot_maximum) pcm->fuel.blm_cells[i] = cal->boot_maximum;
        if (pcm->fuel.blm_cells[i] < cal->boot_minimum) pcm->fuel.blm_cells[i] = cal->boot_minimum;
    }
    return PCM_OK;
}
