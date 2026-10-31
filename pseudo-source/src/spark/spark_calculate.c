#include "spark.h"
/* A700..AB43, under the explicit optional1812 dependency. Admission and the
 * AB44 period/EST output conversion remain outside this command builder. */
PcmStatus pcm_spark_calculate(Pcm *pcm)
{
    PcmStatus result = pcm_spark_composite(pcm);
    return result == PCM_OK ? pcm_spark_command(pcm) : result;
}
