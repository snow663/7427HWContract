#include "spark.h"
#include "knock.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* A9E0..AB43: extension, resident override, upper limit, knock, lower, service. */
PcmStatus pcm_spark_command(Pcm *pcm)
{
    RUN(pcm_spark_extension(pcm));
    RUN(pcm_spark_override(pcm));
    RUN(pcm_spark_upper_limit(pcm));
    RUN(pcm_knock_corrections(pcm));
    RUN(pcm_spark_lower_limit(pcm));
    return pcm_spark_service(pcm);
}
