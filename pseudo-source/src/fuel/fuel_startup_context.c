#include "fuel.h"
#include "mixture_internal.h"
#include "hardware.h"
/* E38F..E3BA. Low003F nibble only; existing upper-bit owners are preserved.
 * SEI/CLI are literal assignments, including failure-prefix behavior. */
PcmStatus pcm_fuel_startup_context(Pcm *pcm)
{
    MIX_RUN(pcm_mask_irq(pcm, true));
    MIX_CAL();
    uint8_t old = pcm->fuel.startup_previous_rpm, now = pcm->spark.rpm_high;
    uint8_t flags = old < now ? 1 : 0;
    uint8_t magnitude = old < now ? (uint8_t)(now - old) : (uint8_t)(old - now);
    if (magnitude >= cal->startup_rpm_delta) flags |= 2u;
    pcm->fuel.startup_previous_rpm = pcm->spark.rpm_high;
    if (pcm->iac.rpm_error > cal->startup_effort) flags |= 8u;
    if (pcm->iac.context & 0x80u) flags |= 4u;
    pcm->fuel.startup_context = flags;
    return pcm_mask_irq(pcm, false);
}
