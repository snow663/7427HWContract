#include "startup.h"
#include "system.h"
#define RUN(call) do { PcmStatus result=(call);if (result!=PCM_OK) return result; } while (0)
/*718A..71C2. C56F retains its literal SEI/CLI and publishes battery after CLI. */
PcmStatus pcm_reset_sensors(Pcm *pcm)
{
    RUN(pcm_adc_auxiliary(pcm));
    RUN(pcm_adc_inputs(pcm));
    RUN(pcm_battery_input(pcm));
    return pcm_factory_admit(pcm);
}
