#include "spark.h"
/* A5E5..A6FF: ordered period sample, RPM/filter producers and timing terms. */
PcmStatus pcm_spark_precompute(Pcm *pcm)
{
    PcmStatus result = pcm_spark_period_sample(pcm);
    if (result != PCM_OK) return result;
    result = pcm_spark_rpm_filters(pcm);
    return result == PCM_OK ? pcm_spark_period_terms(pcm) : result;
}
