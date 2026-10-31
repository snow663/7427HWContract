#include "spark.h"
/* A9E0..A9E6: optional external1812 code is not supplied by the resident ROM.
 * This host dependency interface does not define that module's machine ABI. */
PcmStatus pcm_spark_extension(Pcm *pcm)
{
    if (!pcm->scheduler.profiling_enabled) return PCM_OK; /* Same RAM0086.6. */
    return pcm_run_task(pcm, PCM_SPARK_EXTENSION);
}
