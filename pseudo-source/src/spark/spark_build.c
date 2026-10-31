#include "spark.h"
/* A466..AB43 on normal continuation, under AC51/1812 dependencies. Report a
 * complete new normal command separately from alternate success or errors. */
PcmStatus pcm_spark_build(Pcm *pcm, bool *built)
{
    if (built == NULL) return PCM_BAD_CONFIGURATION;
    *built = false;
    bool normal;
    PcmStatus result = pcm_spark_prepare(pcm, &normal);
    if (result != PCM_OK || !normal) return result;
    result = pcm_spark_precompute(pcm);
    if (result != PCM_OK) return result;
    result = pcm_spark_calculate(pcm);
    if (result == PCM_OK) *built = true;
    return result;
}
