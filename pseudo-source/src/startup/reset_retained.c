#include "startup.h"
#include "system.h"
#define RUN(call) do { PcmStatus result=(call);if (result!=PCM_OK) return result; } while (0)
/*71C3..7392; controller initialization starts at7393, not inside STAB7391. */
PcmStatus pcm_reset_retained(Pcm *pcm)
{
    RUN(pcm_boot_rom_validate(pcm));
    RUN(pcm_boot_retained_validate(pcm));
    RUN(pcm_boot_adaptive_validate(pcm));
    return pcm_boot_recovery(pcm);
}
