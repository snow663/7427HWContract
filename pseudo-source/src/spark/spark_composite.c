#include "spark.h"
/* A700..A9DF: known contiguous composite body, before extension and limits. */
PcmStatus pcm_spark_composite(Pcm *pcm)
{
    PcmStatus result = pcm_spark_terms(pcm);
    return result == PCM_OK ? pcm_spark_modifiers(pcm) : result;
}
