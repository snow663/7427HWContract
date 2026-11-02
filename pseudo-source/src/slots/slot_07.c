#include "scheduler.h"
#include "control.h"
#include "spark.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)
/* 7B1B..7B2A. Preserve the five resident calls and their original cadence.
 * All five resident bodies run directly; signature-qualified180C stays explicit. */
PcmStatus pcm_slot_07(Pcm *pcm)
{
    RUN(pcm_transmission_outputs(pcm));
    RUN(pcm_connection_probe(pcm));
    RUN(pcm_iac_background(pcm));
    RUN(pcm_spark_auxiliary(pcm));
    return pcm_shift_lamp(pcm);
}
