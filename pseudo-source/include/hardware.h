#ifndef PSEUDO_SOURCE_HARDWARE_H
#define PSEUDO_SOURCE_HARDWARE_H
#include "pcm.h"

/* Literal addresses from verified stock instructions. Their identities follow
 * the F1-style map; physical board decode/ASIC semantics remain explicit. */
enum {
    PCM_TCNT = 0x300e, PCM_TOC1 = 0x3016, PCM_TOC3 = 0x301a,
    PCM_TMSK1 = 0x3022, PCM_TFLG1 = 0x3023,
    PCM_BAUD = 0x302b, PCM_SCCR1 = 0x302c, PCM_SCCR2 = 0x302d,
    PCM_SCSR = 0x302e, PCM_SCDR = 0x302f,
    PCM_COPRST = 0x303a, PCM_BOARD_HEARTBEAT = 0x3066,
    PCM_CURRENT_COMMAND = 0x3068,
    PCM_INJECTOR_WORD = 0x3fce, PCM_SPARK_WORD = 0x3fdc
};
PcmStatus pcm_watchdog_service(Pcm *);
PcmStatus pcm_heartbeat_toggle(Pcm *);
PcmStatus pcm_timer_arm(Pcm *);
PcmStatus pcm_reference_irq(Pcm *);
PcmStatus pcm_oc1_irq(Pcm *);
PcmStatus pcm_sci_irq(Pcm *);
PcmStatus pcm_reset_sequence(Pcm *, const PcmPlatform *, const PcmCalibration *);
#endif
