#include "spark.h"
#include "hardware.h"
/* A5C6..A5D9: ordered timeout prefix ending at the first SWI. This status is
 * a host boundary, not a C return substituted for target SWI/frame/trap work. */
PcmStatus pcm_spark_timeout(Pcm *pcm)
{
    pcm->runtime.fuel_running = false;
    pcm->runtime.spark_running = false;
    pcm->spark.first_reference = false;
    pcm->spark.period_basis = UINT16_MAX;
    PcmStatus result = pcm_update8(pcm, PCM_BOARD_3060, 0x10u, 0);
    return result == PCM_OK ? PCM_TRAP_BOUNDARY : result;
}
