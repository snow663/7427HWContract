#include "spark.h"
#include "hardware.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* AB89..ABCA: stack-saved word becomes a C local. F3ED is literal RTS,
 * so no artificial delay callback is inserted between these transactions. */
PcmStatus pcm_spark_handoff(Pcm *pcm, uint16_t saved)
{
    uint16_t period, rolling1, rolling2, work;
    RUN(pcm_read16(pcm, PCM_REFERENCE_PERIOD, &period));
    uint16_t anchor = (uint16_t)(((uint16_t)(0u - period) >> 4) | 0xf000u);
    RUN(pcm_read16(pcm, PCM_SPARK_ROLLING, &rolling1));
    uint16_t candidate = (uint16_t)(anchor + rolling1);
    uint16_t chosen = ((uint16_t)(candidate - saved) & 0x8000u) ? saved : candidate;
    RUN(pcm_read16(pcm, PCM_SPARK_ROLLING, &rolling2));
    uint16_t first = (uint16_t)(chosen - rolling2);
    RUN(pcm_write16(pcm, PCM_SPARK_TIMING_A, first));
    RUN(pcm_read16(pcm, PCM_SPARK_WORD, &work));
    uint16_t second = (uint16_t)(first + work - pcm->spark.period_correction);
    uint16_t correction = pcm->spark.period_correction; /* ABB7, before the next write. */
    RUN(pcm_write16(pcm, PCM_SPARK_TIMING_B, second));
    RUN(pcm_write16(pcm, PCM_SPARK_WORD, correction));
    return pcm_write16(pcm, PCM_SPARK_ROLLING, chosen);
}
