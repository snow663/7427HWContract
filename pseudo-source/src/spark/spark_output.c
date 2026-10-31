#include "spark.h"
/* AB44..ABCA, stopping before the post-publication monitor at ABCB. */
PcmStatus pcm_spark_output(Pcm *pcm)
{
    uint16_t saved;
    PcmStatus result = pcm_spark_convert(pcm, &saved);
    return result == PCM_OK ? pcm_spark_handoff(pcm, saved) : result;
}
