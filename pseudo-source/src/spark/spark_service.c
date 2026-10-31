#include "spark.h"
/* AB1A..AB43: service edits happen after limits, then both common RAM stores.
 * No calibration or hardware binding is used. Do not re-clamp the result. */
PcmStatus pcm_spark_service(Pcm *pcm)
{
    uint16_t command = pcm->spark.command;
    if (pcm->runtime.engine_service && (pcm->spark.service_flags & 0x08u)) {
        if (!(pcm->spark.service_flags & 0x10u)) command = 0;
        bool subtract = (pcm->spark.service_flags & 0x20u) != 0;
        uint8_t amount = pcm->spark.service_amount;
        command = subtract ? (uint16_t)(command - amount) : (uint16_t)(command + amount);
    }
    pcm->spark.command = command;
    pcm->spark.command_latched = command;
    return PCM_OK;
}
