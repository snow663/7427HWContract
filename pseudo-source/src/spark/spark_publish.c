#include "spark.h"
/* Conditional A466..ABCA publication, with an explicit completion result.
 * The resident controller adds the monitor after successful normal publication. */
PcmStatus pcm_spark_publish(Pcm *pcm, bool *published)
{
    if (published == NULL) return PCM_BAD_CONFIGURATION;
    *published = false;
    bool built;
    PcmStatus result = pcm_spark_build(pcm, &built);
    if (result != PCM_OK || !built) return result;
    result = pcm_spark_output(pcm);
    if (result == PCM_OK) *published = true;
    return result;
}
