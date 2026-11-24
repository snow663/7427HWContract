#include "adaptive_cells_internal.h"
/* B9EE. Reset three 17-cell adaptive banks to 80 and maintain their checksum. */
PcmStatus pcm_transmission_adaptive_reset(Pcm *pcm)
{
    return adaptive_cells(pcm, false);
}
