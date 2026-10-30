#include "scheduler.h"
#include "hardware.h"
#include "control.h"
#define RUN(call) do { PcmStatus result = (call); if (result != PCM_OK) return result; } while (0)

/* Reference 79D9..7A44. Fields are sampled at their own gates. Callees may
 * change state. This is an ordered source outline, not an instruction trace. */
PcmStatus pcm_dispatch_fast(Pcm *pcm)
{
    if (pcm->runtime.special_fast_group) {
        if (pcm->scheduler.phase & 1u) {
            RUN(pcm_alternate_rpm(pcm));
            RUN(pcm_watchdog_service(pcm));
        }
        return PCM_OK;
    }
    RUN(pcm_common_io(pcm));
    if (!(pcm->scheduler.phase & 1u)) {
        RUN(pcm_input_housekeeping(pcm));
        RUN(pcm_spark_control(pcm));
        RUN(pcm_egr_feedback(pcm));
        RUN(pcm_egr_control(pcm));
        RUN(pcm_serial_poll(pcm));
        if ((pcm->scheduler.phase & 3u) == 0) {
            RUN(pcm_egr_flow(pcm));
            RUN(pcm_transmission_input(pcm));
        } else RUN(pcm_pressure_tcc(pcm));
    } else {
        RUN(pcm_fuel_control(pcm));
        RUN(pcm_egr_output(pcm));
        if (pcm->runtime.engine_service && pcm->runtime.inhibit_heartbeat) {
            pcm->runtime.output_override = true;
            pcm->runtime.first_conversion = true;
        } else RUN(pcm_heartbeat_toggle(pcm));
        if ((pcm->scheduler.phase & 3u) == 1) RUN(pcm_shift_control(pcm));
        else {
            RUN(pcm_iac_control(pcm));
            RUN(pcm_transmission_spark(pcm));
        }
    }
    return PCM_OK;
}
