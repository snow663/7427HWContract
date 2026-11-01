#include "control.h"
#include "spark.h"
/* Reference AC51: Alternate reference-period RPM and board-request path.
 * Resident adapter; it no longer requires a platform task binding. */
PcmStatus pcm_alternate_rpm(Pcm *pcm)
{
    return pcm_spark_alternate(pcm);
}
