#include "spark.h"
/* A466..A5E4: load coordinates, MAP check and reference/run admission. Normal
 * continuation stops at A5E5; AC51 stays explicit and SWI stops at a boundary. */
PcmStatus pcm_spark_prepare(Pcm *pcm, bool *normal)
{
    if (normal == NULL) return PCM_BAD_CONFIGURATION;
    *normal = false;
    PcmStatus result = pcm_spark_load(pcm);
    if (result != PCM_OK) return result;
    result = pcm_spark_map_check(pcm);
    return result == PCM_OK ? pcm_spark_admit(pcm, normal) : result;
}
