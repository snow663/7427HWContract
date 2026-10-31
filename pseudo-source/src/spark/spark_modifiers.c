#include "spark.h"
/* A84E..A9DF, ending before the external1812/special-override boundary. */
PcmStatus pcm_spark_modifiers(Pcm *pcm)
{
    PcmStatus result = pcm_spark_idle(pcm);
    if (result == PCM_OK) result = pcm_spark_transient(pcm);
    if (result == PCM_OK) result = pcm_spark_decel(pcm);
    return result;
}
