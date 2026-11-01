#include "control.h"
#include "spark.h"
/* A466..ACA6 resident body. An alternate return has already performed its
 * cleanup; only completed normal publication proceeds to the EST monitor. */
PcmStatus pcm_spark_control(Pcm *pcm)
{
    bool published;
    PcmStatus result = pcm_spark_publish(pcm, &published);
    if (result != PCM_OK || !published) return result;
    return pcm_spark_monitor(pcm);
}
