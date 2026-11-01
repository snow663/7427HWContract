#ifndef PSEUDO_SOURCE_HARDWARE_H
#define PSEUDO_SOURCE_HARDWARE_H
#include "pcm.h"

/* Literal addresses from verified stock instructions. Their identities follow
 * the F1-style map; physical board decode/ASIC semantics remain explicit. */
enum {
    PCM_PORTA = 0x3000, PCM_DDRA = 0x3001, PCM_DDRG = 0x3003,
    PCM_PORTD = 0x3008, PCM_DDRD = 0x3009, PCM_CFORC = 0x300b,
    PCM_OC1M = 0x300c, PCM_OC1D = 0x300d,
    PCM_TCNT = 0x300e, PCM_TOC1 = 0x3016, PCM_TOC3 = 0x301a,
    PCM_TOC4 = 0x301c, PCM_TOC5 = 0x301e, PCM_TCTL1 = 0x3020,
    PCM_TCTL2 = 0x3021, PCM_PACTL = 0x3026, PCM_SPCR = 0x3028,
    PCM_TMSK1 = 0x3022, PCM_TFLG1 = 0x3023,
    PCM_BAUD = 0x302b, PCM_SCCR1 = 0x302c, PCM_SCCR2 = 0x302d,
    PCM_SCSR = 0x302e, PCM_SCDR = 0x302f,
    PCM_ADCTL = 0x3030, PCM_ADR1 = 0x3031, PCM_ADR4 = 0x3034,
    PCM_COPRST = 0x303a, PCM_HPRIO = 0x303c, PCM_TEST1 = 0x303e,
    PCM_CSSTRH = 0x305c, PCM_CSCTL = 0x305d,
    PCM_CSGADR = 0x305e, PCM_CSGSIZ = 0x305f,
    PCM_BOARD_3060 = 0x3060, PCM_BOARD_3061 = 0x3061, PCM_REFERENCE_STROBE = 0x3062,
    PCM_BOARD_3063 = 0x3063, PCM_BOARD_3065 = 0x3065,
    PCM_BOARD_HEARTBEAT = 0x3066, PCM_BOARD_306E = 0x306e,
    PCM_REFERENCE_AGE = 0x306f, PCM_BOARD_CONTROL = 0x3ffc,
    PCM_CURRENT_COMMAND = 0x3068,
    PCM_REFERENCE_PERIOD = 0x3fc0, PCM_KNOCK_COUNTER = 0x3fc8,
    PCM_INJECTOR_WORD = 0x3fce, PCM_SPARK_WORD = 0x3fdc,
    PCM_SPARK_TIMING_A = 0x3fe8, PCM_SPARK_TIMING_B = 0x3fe6, PCM_SPARK_ROLLING = 0x3ff6,
    PCM_ASYNC_PACKET = 0x3ff2, PCM_REFERENCE_STATUS = 0x3ffa
};
PcmStatus pcm_watchdog_service(Pcm *);
PcmStatus pcm_heartbeat_toggle(Pcm *);
PcmStatus pcm_timer_arm(Pcm *);
PcmStatus pcm_reference_irq(Pcm *);
PcmStatus pcm_reference_prefix(Pcm *);
PcmStatus pcm_reference_event(Pcm *);
PcmStatus pcm_reference_crank(Pcm *);
PcmStatus pcm_reference_run(Pcm *);
PcmStatus pcm_reference_common(Pcm *);
PcmStatus pcm_reference_decay(Pcm *);
PcmStatus pcm_reference_bank_guard(Pcm *);
PcmStatus pcm_reference_crank_timer(Pcm *);
PcmStatus pcm_reference_timer_arm(Pcm *, bool bank_b);
PcmStatus pcm_fuel_async(Pcm *, uint16_t pulse);
PcmStatus pcm_delay_cycles(Pcm *, uint16_t cycles);
PcmStatus pcm_update8(Pcm *, uint16_t address, uint8_t clear, uint8_t set);
PcmStatus pcm_adc_mux(Pcm *, uint8_t selector);
PcmStatus pcm_adc_convert(Pcm *, uint8_t control);
PcmStatus pcm_oc1_irq(Pcm *);
PcmStatus pcm_sci_irq(Pcm *);
PcmStatus pcm_reset_sequence(Pcm *, const PcmPlatform *, const PcmCalibration *);
#endif
