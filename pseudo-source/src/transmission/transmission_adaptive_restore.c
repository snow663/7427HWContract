#include "adaptive_cells_internal.h"
/* B99F. Restore three 17-cell adaptive banks from their ROM tables and maintain their checksum. */
PcmStatus pcm_transmission_adaptive_restore(Pcm *pcm)
{
    return adaptive_cells(pcm, true);
}
