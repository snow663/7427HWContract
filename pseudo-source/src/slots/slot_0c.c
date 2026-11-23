#include "scheduler.h"
#include "board_io.h"

/* 7B44..7B47. */
PcmStatus pcm_slot_0c(Pcm *pcm)
{
    return pcm_slow_register_service(pcm);
}
