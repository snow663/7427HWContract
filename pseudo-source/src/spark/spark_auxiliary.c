#include "spark.h"
#include "knock.h"
/* CA6B..CB14, now complete as a callable body. Other slot7 callees remain delegated. */
PcmStatus pcm_spark_auxiliary(Pcm *pcm)
{
    PcmStatus result = pcm_spark_mat(pcm);
    if (result == PCM_OK) result = pcm_spark_pe(pcm);
    if (result == PCM_OK) result = pcm_knock_gains(pcm);
    return result;
}
