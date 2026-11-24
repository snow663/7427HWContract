#include "fuel.h"

/* BMHM $7D4B..$7E4E contiguous scheduled-fuel prefix. A nonreturning
 * ignition trap or missing optional governor stops here before crank/run
 * admission. The broad $7D4B fuel task is not replaced until the $852C
 * scheduled tail and complete caller integration are implemented. */
PcmStatus pcm_fuel_input_prefix(Pcm *pcm)
{
    PcmStatus status=pcm_fuel_ignition_precheck(pcm);
    return status==PCM_OK ? pcm_fuel_input_precalculate(pcm) : status;
}
