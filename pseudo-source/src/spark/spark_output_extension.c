#include "spark.h"
/* AB62..AB68: the unsupplied180F module receives/returns magnitude in A.
 * The C payload is a host interface, not a reconstructed machine ABI. */
PcmStatus pcm_spark_output_extension(Pcm *pcm, uint8_t *magnitude)
{
    if (magnitude == NULL) return PCM_BAD_CONFIGURATION;
    if (!pcm->scheduler.profiling_enabled) return PCM_OK;
    pcm->spark.extension_magnitude = *magnitude;
    PcmStatus result = pcm_run_task(pcm, PCM_SPARK_OUTPUT_EXTENSION);
    if (result == PCM_OK) *magnitude = pcm->spark.extension_magnitude;
    return result;
}
