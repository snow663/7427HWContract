#include "control.h"
/* Reference A466: Load conversion reference consumption and spark-control group.
 * Contract boundary: body not ported. An explicit platform binding is required. */
PcmStatus pcm_spark_control(Pcm *pcm)
{
    return pcm_run_task(pcm, PCM_SPARK_CONTROL);
}
