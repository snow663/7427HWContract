#include "slot4_monitor.h"
/* C8B1 Common slot 04 diagnostic group in stock call order. */
PcmStatus pcm_diagnostic_slot_04(Pcm *pcm)
{
    /* EE5F/EE60 and EB17/EB18 are literal RTS entries in this image. */
    SYS_RUN(pcm_diagnostic_solenoid_81(pcm));
    SYS_RUN(pcm_diagnostic_solenoid_82(pcm));
    SYS_RUN(pcm_diagnostic_solenoid_83(pcm));
    SYS_RUN(pcm_diagnostic_battery_52(pcm));
    SYS_RUN(pcm_diagnostic_battery_53(pcm));
    SYS_RUN(pcm_diagnostic_battery_compensated(pcm));
    SYS_RUN(pcm_diagnostic_baro_adc_high(pcm));
    return pcm_diagnostic_baro_adc_low(pcm);
}
