#ifndef PSEUDO_SOURCE_PCM_H
#define PSEUDO_SOURCE_PCM_H

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

/* Source-level contracts only. No target ABI, vector prologue, or final RAM
 * placement is implied by compiling this host-checkable outline. */
typedef enum {
    PCM_OK = 0, PCM_UNIMPLEMENTED, PCM_NO_HARDWARE, PCM_BAD_CONFIGURATION,
    PCM_FACTORY_BOUNDARY, PCM_STACK_BOUNDARY
} PcmStatus;

typedef enum {
    PCM_COMMON_IO, PCM_INPUT_HOUSEKEEPING, PCM_SPARK_CONTROL,
    PCM_EGR_FEEDBACK, PCM_EGR_CONTROL, PCM_SERIAL_POLL, PCM_EGR_FLOW,
    PCM_TRANSMISSION_INPUT, PCM_PRESSURE_TCC, PCM_FUEL_CONTROL,
    PCM_EGR_OUTPUT, PCM_SHIFT_CONTROL, PCM_IAC_CONTROL,
    PCM_TRANSMISSION_SPARK, PCM_ALTERNATE_RPM,
    PCM_IAC_STEP, PCM_ADC_FEEDBACK, PCM_CURRENT_CONTROL,
    PCM_SLOT_00, PCM_SLOT_01, PCM_SLOT_02, PCM_SLOT_03,
    PCM_SLOT_04, PCM_SLOT_05, PCM_AC_SWITCH_INPUTS, PCM_SLOT_07,
    PCM_SLOT_09, PCM_SLOT_0A, PCM_SLOT_0B,
    PCM_SLOT_0C, PCM_SLOT_0D, PCM_SLOT_0E, PCM_SLOT_0F,
    PCM_SCI_BODY,
    PCM_RESET_ENTRY, PCM_RESET_RAM,
    PCM_RESET_SENSORS, PCM_RESET_RETAINED, PCM_RESET_CONTROLLERS,
    PCM_RESET_SERIAL, PCM_TASK_COUNT
} PcmTask;

struct Pcm;
typedef PcmStatus (*PcmRoutine)(struct Pcm *);
typedef PcmStatus (*PcmDependency)(struct Pcm *, PcmTask);
typedef struct {
    void *context;
    PcmStatus (*read8)(void *, uint16_t address, uint8_t *);
    PcmStatus (*read16)(void *, uint16_t address, uint16_t *);
    PcmStatus (*write8)(void *, uint16_t address, uint8_t);
    PcmStatus (*write16)(void *, uint16_t address, uint16_t);
    /* Literal mask assignment, not save/restore critical-section nesting. */
    PcmStatus (*mask_irq)(void *, bool masked);
    /* Minimum nominal E-cycle delay for REF ADC sampling. Preserve the
     * caller's IRQ mask; target call overhead is budgeted separately. */
    PcmStatus (*delay_cycles)(void *, uint16_t cycles);
    /* Must establish the documented entry-stack precondition. Target stack
     * guard/recovery is deliberately delegated, not simulated with C SP. */
    PcmStatus (*check_stack)(void *, bool busy);
    PcmDependency task[PCM_TASK_COUNT];
} PcmPlatform;

typedef struct {
    uint8_t mode_b, mode_c, mode_e, diagnostic_options;
    uint8_t crank_skip[17], decay_temperature[17], decay_event[17];
    uint8_t crank_cold[24], crank_warm[24], crank_hot[24], crank_repeat[8];
    uint8_t short_pulse[17];
    uint8_t crank_timer_gain, decay_interval, crank_age_cap, battery_limit;
    uint8_t coolant_gain_threshold, bank_guard_limit;
    uint8_t load_minimum, throttle_limit, load_event_gain;
    uint16_t short_subtract, running_packet_minimum;
} PcmReferenceCalibration;

typedef struct {
    uint8_t noise_floor[64];           /* stock 45DB..461A */
    uint8_t observation_bias[64];      /* stock 461C..465B */
    uint8_t decay_rate[17];            /* stock 45A5..45B5 */
    uint8_t minimum_speed, minimum_rpm_high, minimum_coolant; /* 45D8..45DA */
    uint8_t sensor_fault_delay, sensor_upper, sensor_lower, fault_retard; /* 4E74..4E77 */
    uint8_t event_gain_curve[17], pe_retard_cap[8], cruise_retard_cap[7]; /* 4594,4585,458D */
    uint8_t octane_rpm[9], octane_load[17]; /* 45BE,45C7; bounded RPM input uses 9 knots */
    uint8_t learn_min_coolant, learn_min_load, learn_load_change_limit; /* 45B6..45B8 */
    uint8_t learn_high_retard, learn_low_retard, learn_increment, learn_decrement, learn_scale; /* 45B9..45BD */
    uint8_t burst_load_limit, burst_throttle_limit, burst_throttle_delta, burst_duration; /* 46DF..46E2 */
    uint8_t burst_table_limit, burst_curve[11]; /* 46E3..46EE; lookup input is at most 152 */
} PcmKnockCalibration;

typedef struct {
    uint8_t row_offset, column_offset, stride;
    uint16_t length;
    const uint8_t *values;
} PcmTable2D;

typedef struct {
    PcmTable2D base_normal, base_idle, coolant, altitude, mat, egr;
    uint8_t coolant_mode, mat_mode, egr_mode, egr_gain;
    uint8_t base_bias, coolant_bias, altitude_bias, egr_bias, mat_bias;
    uint8_t idle_coolant_threshold, transmission_bias;
    uint8_t mat_negative_gain[17], mat_positive_gain[17], pe_curve[17];
} PcmSparkCalibration;

typedef struct {
    uint16_t format_version;
    uint16_t recurring_compare_counts;
    uint16_t first_compare_counts;
    uint16_t run_counter_clear_threshold;
    uint16_t board_startup_word;
    uint16_t reference_compare_counts[64]; /* stock words465D..46DC */
    uint8_t initial_phase;
    uint8_t mode_f;                    /* stock400F, shared feature-selection byte */
    uint8_t mode_d;                    /* stock400D, altitude uses bit2 */
    PcmReferenceCalibration reference;
    PcmKnockCalibration knock;
    const PcmSparkCalibration *spark;   /* immutable source profile, not a serialized pointer */
} PcmCalibration;

typedef struct {
    volatile uint8_t phase;            /* reference RAM0002 */
    volatile uint8_t busy_phase;       /* RAM0003 */
    volatile bool busy;                /* RAM004F.2 */
    volatile bool pending;             /* RAM003A.5: one bit, never a queue */
    bool timer_seen;                   /* RAM0000.0 */
    bool profiling_enabled;            /* RAM0086.6 */
    uint16_t peak_counts[16];          /* reference RAM02D3..02F2 */
    bool epoch_toggle;                 /* RAM0043.5 */
    uint16_t run_counter;              /* RAM00FD */
    bool clear_after_run_count;        /* RAM0004.4 */
} PcmScheduler;

typedef struct {
    bool factory_mode;                 /* RAM0044.0 */
    bool special_fast_group;           /* RAM001A.5 */
    bool fuel_running;                 /* RAM004F.4 */
    bool spark_running;                /* RAM004F.7 */
    bool ignition_off;                 /* RAM0051.3 */
    bool engine_service;               /* RAM003B.4 */
    bool transmission_service;         /* RAM003B.3 */
    bool service_output_enable;        /* RAM038F.2 */
    bool service_output_value;         /* RAM0390.2 */
    bool service_output_mirror;        /* RAM0072.7 */
    bool inhibit_heartbeat;            /* RAM0391.7 */
    bool monitor_freeze;               /* RAM003B.2 */
    bool output_override;              /* RAM0044.2 */
    bool first_conversion;             /* RAM0043.7 */
    bool refresh_requested;            /* RAM0051.2 */
    bool refresh_late;                 /* RAM0004.2 */
    uint8_t current_output;            /* RAM014C */
    volatile uint8_t primary_faults;   /* RAM0016; normal KR tests bits60 */
    volatile bool adc_timeout;         /* RAM001A.1; cleared before each F25F conversion */
    volatile bool adc_fault;           /* RAM003A.0; timeout sets, success retains */
    volatile bool power_enrichment;    /* RAM003D.5 */
    volatile bool diagnostic_switch;   /* RAM0050.4, produced by CB15 input boundary */
} PcmRuntime;

typedef struct {
    volatile uint8_t rpm_coordinate;    /* RAM0062, not engineering RPM */
    volatile bool latch_inhibited;     /* RAM0044.4, distinct from0051.3 */
    volatile bool pending;             /* RAM0050.5: one bit, never a count */
    volatile bool sample_map;          /* RAM0050.0 */
    volatile uint8_t map_sample;        /* RAM082E */
    volatile uint8_t coolant, battery, load_coordinate, throttle; /* 0006,0055,0067,01D9 */
    volatile uint16_t load_filtered, load_event; /* 0068,006A */
    volatile uint8_t crank_references, event_age; /* 02CD,02CE */
    volatile uint16_t crank_seed, delivered_pulse, timer_pulse; /* 02CF,024C,0250 */
    volatile uint8_t additive_offset;   /* RAM0256 */
    volatile uint8_t enrichment, enrichment_age, enrichment_decrement, decay_count; /* 02C9,0268,0267,081E */
    volatile uint8_t bank_guard_count;  /* RAM084E */
    volatile bool bank_fault;          /* RAM0019.6 */
    volatile bool crank_timer_latch, split_latch; /* RAM0053.5,0053.6 */
    volatile bool packet_updated, bank_latch; /* RAM0051.0,0051.7 */
    volatile bool extra_request, extra_guard; /* RAM0073.6,003F.4 */
    volatile uint16_t running_packet, timer_delay; /* RAM0254,081F */
    volatile uint16_t compare_a, compare_b, extended_a, extended_b; /* 0821,0823,0825,0827 */
    volatile uint8_t split_count, split_clear; /* RAM0829,082A */
} PcmReference;

typedef struct {
    volatile uint16_t sample_baseline; /* RAM0203, last sampled 3FC8 word */
    volatile uint8_t observation_accumulator; /* RAM020D, not retard degrees */
    volatile uint8_t retard;           /* RAM020C; command subtraction uses this >>1 */
    volatile uint8_t event_gain, retard_limit; /* RAM0843,0844; upstream spark inputs */
    volatile uint8_t sensor_fault_count; /* RAM0207 */
    volatile bool sensor_fault, burst_active; /* RAM0019.4,006E.1 */
    volatile uint8_t burst_gain, burst_countdown; /* RAM0842,020E */
    volatile uint8_t octane_rpm_factor; /* RAM0841 */
    volatile uint8_t activity, scaled_activity, adaptive_retard; /* RAM0209..020B */
    volatile bool learning_high, learning_low; /* RAM0052.0,0052.1 */
} PcmKnock;

typedef struct {
    volatile uint16_t command;         /* RAM01EE, wrapped signed-command representation */
    volatile uint8_t rpm_high;         /* RAM0063, high byte of filtered RPM word */
    volatile uint8_t vehicle_speed_high; /* RAM0284, high byte of filtered VSS word */
    volatile uint8_t load_coordinate, previous_load, vacuum; /* RAM01C0,01C2,01C9 */
    volatile uint8_t previous_throttle; /* RAM01DA; current TPS shares reference.throttle */
    volatile uint8_t load_status;       /* RAM006F; gain/cap producer tests mask48 */
    volatile uint8_t recent_load, rpm_low_coordinate, barometric_pressure; /* 01C1,0061,01CC */
    volatile bool idle_feedback, idle_state; /* RAM0050.6,0050.7, sampled at their own gates */
    volatile uint8_t mat_sample, mat_magnitude, mat_effect; /* RAM022F,01FA,083C */
    volatile bool mat_negative;        /* RAM0041.1 */
    volatile uint8_t base_advance, coolant_advance, altitude_advance, pe_advance; /* 01F8,01F9,01FB,01FC */
    volatile uint16_t egr_filtered, composite; /* RAM01F4,01FD */
    volatile bool egr_active;           /* RAM006E.7 */
    volatile uint8_t egr_fraction_high, pe_fraction; /* RAM01B2 high byte,0278 */
    volatile uint8_t startup_adder, transmission_retard, transmission_status; /* 02CB,015A,00A4 */
} PcmSpark;

typedef struct Pcm {
    const PcmPlatform *platform; /* immutable bindings can live in ROM */
    const PcmCalibration *calibration;
    PcmScheduler scheduler;
    PcmRuntime runtime;
    PcmReference reference;
    PcmKnock knock;
    PcmSpark spark;
    PcmTask unresolved_task;
    void *application;                 /* tests/strategy-owned explicit state */
} Pcm;

/* Subsystem APIs live in separate headers. Each public routine is defined in
 * its own .c file; supporting private helpers may stay with their owner. */
PcmStatus pcm_run_task(Pcm *, PcmTask);
PcmStatus pcm_read8(Pcm *, uint16_t, uint8_t *);
PcmStatus pcm_read16(Pcm *, uint16_t, uint16_t *);
PcmStatus pcm_write8(Pcm *, uint16_t, uint8_t);
PcmStatus pcm_write16(Pcm *, uint16_t, uint16_t);
PcmStatus pcm_mask_irq(Pcm *, bool);

#endif
