#include "spark.h"
#include "knock.h"
#define RUN(call) do { PcmStatus status = (call); if (status != PCM_OK) return status; } while (0)
/* A700..A84D: contiguous command construction up to the idle-spark gate. */
PcmStatus pcm_spark_terms(Pcm *pcm)
{
    RUN(pcm_spark_base(pcm));
    RUN(pcm_spark_coolant(pcm));
    RUN(pcm_spark_altitude(pcm));
    RUN(pcm_low_octane_retard(pcm));
    RUN(pcm_spark_egr(pcm));
    RUN(pcm_spark_sum(pcm));
    return pcm_spark_mat_effect(pcm);
}
