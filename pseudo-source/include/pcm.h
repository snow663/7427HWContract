#ifndef PSEUDO_SOURCE_PCM_H
#define PSEUDO_SOURCE_PCM_H

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

/* Source-level contracts only. No target ABI, vector prologue, or final RAM
 * placement is implied by compiling this host-checkable outline. */
typedef enum {
    PCM_OK = 0, PCM_UNIMPLEMENTED, PCM_NO_HARDWARE, PCM_BAD_CONFIGURATION,
    PCM_FACTORY_BOUNDARY, PCM_STACK_BOUNDARY, PCM_TRAP_BOUNDARY
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
    PCM_RESET_SERIAL, PCM_SPARK_EXTENSION, PCM_SPARK_OUTPUT_EXTENSION,
    PCM_CONNECTION_EXTENSION, PCM_IAC_BACKGROUND, PCM_SHIFT_LAMP,
    PCM_EGR_DEMAND, PCM_VSS_FILTER, PCM_IAC_EXTENSION, PCM_TASK_COUNT
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
    /* Minimum nominal E-cycle delay for ADC/board sequences. Preserve the
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
    uint8_t limit, length;
    const uint8_t *values;
} PcmCappedCurve;

typedef struct {
    uint16_t length;
    uint8_t scale;
    const uint8_t *values;
} PcmScaledCurve;

typedef struct {
    uint8_t offset, limit;
    PcmScaledCurve curve;
} PcmOffsetCurve;

typedef struct {
    PcmTable2D base_normal, base_idle, coolant, altitude, mat, egr;
    uint8_t coolant_mode, mat_mode, egr_mode, egr_gain;
    uint8_t base_bias, coolant_bias, altitude_bias, egr_bias, mat_bias;
    uint8_t idle_coolant_threshold, transmission_bias;
    uint8_t mat_negative_gain[17], mat_positive_gain[17], pe_curve[17];
    PcmCappedCurve idle_negative_speed, idle_negative_load, idle_positive_speed, idle_positive_load;
    uint16_t idle_runtime_minimum;     /* 415E */
    uint8_t idle_speed_limit, idle_throttle_entry, idle_throttle_retained, idle_coolant_minimum, idle_target_adder; /* 415A..4160 */
    uint8_t idle_bias, idle_positive_cap, idle_derivative_curve[17]; /* 4514,4515,451B */
    uint8_t transient_coolant_minimum, transient_coolant_maximum, transient_gain[5]; /* 46F2..46F8 */
    uint8_t transient_positive[3], transient_negative[3]; /* 46EC..46F1: gain,offset,cap */
    uint8_t recovery_gain, recovery_fast_gain, recovery_throttle, decel_base; /* 414F..4152 */
    uint8_t reference_bias, override_options, override_coolant_minimum; /* 4132,4E90,4161 */
    uint8_t override_throttle_entry, override_throttle_retained; /* 4164,4165 */
    uint16_t override_command;          /* 4162 */
    uint16_t upper_limit, lower_normal, lower_recovery, lower_transmission, lower_transmission_state; /* 4144..414D */
    uint16_t spark_run_period_limit, fuel_run_period_limit, no_reference_age_limit; /* 4133,4135,4962 */
    uint8_t spark_run_events, fuel_run_events, startup_gain; /* 4142,4143,414E */
    uint8_t map_sample_minimum, map_rpm_minimum, map_count_limit, map_throttle_limit; /* 4E64..4E67 */
    uint8_t missing_reference_age_cap; /* 4D96 */
    uint8_t period_scale, rpm_filter_gain, load_filter_gain, monitor_filter_gain; /* 4141,4153,4517,50E4 */
    PcmCappedCurve output_latency;      /* 454A header, 454B..4558 reachable backing */
    uint8_t bypass_options, bypass_delta_limit, bypass_count_limit; /* 5B03,4E71,4E72 */
} PcmSparkCalibration;

typedef struct {
    uint16_t gear_pattern_length;
    const uint8_t *gear_patterns;      /* B319 + raw byte gear index */
} PcmTransmissionCalibration;

typedef struct {
    uint8_t options, startup_rpm_gain, movement_speed_limit, movement_gain;
    uint8_t rpm_curve[4][17], rough_gain, rough_limit, battery_threshold, battery_gain, battery_limit;
    uint8_t blm_limit, blm_count_limit, blm_coolant_minimum, blm_adder[4];
    uint8_t switch_threshold[2], switch_up_delay, switch_down_delay, stall_factor[4];
    uint8_t cold_decay_gain, cold_gain[2], cold_delay_curve[17], cold_runtime_curve[6];
    uint8_t cold_upper[2], cold_lower[2], warm_error_limit, warm_coolant_minimum, warm_coolant_maximum;
    uint8_t ac_difference_lower[2], ac_difference_upper[2], drive_park_delta, park_drive_delta;
    uint8_t ac_decay_amount, ac_decay_reload, dfco_decay_amount, dfco_decay_reload;
    uint8_t kicker_coolant_minimum, kicker_speed_limit, kicker_throttle_limit, kicker_cold_reload;
    uint8_t kicker_baro_entry, kicker_baro_exit, kicker_integral_limit, kicker_flow_limit;
    uint8_t kicker_error_limit[2], kicker_on_reload, kicker_tps_adder, kicker_off_match;
    PcmScaledCurve follower_rpm;
    uint8_t follower_coolant[17], follower_cap[2], follower_park_gain;
    uint8_t follower_drive_hold[12], follower_drive_gain[12], follower_minimum[17];
    uint8_t follower_change_limit, follower_load_limit, follower_low_load_gain, follower_age_limit;
    uint8_t hotstart_coolant_minimum, hotstart_coolant_maximum;
    uint16_t hotstart_runtime_limit;
    uint8_t follower_extended_gain[2], follower_start_minimum_gain, follower_start_flow_gain;
    uint8_t switch_decay_amount, switch_decay_reload, startup_flow_reload, startup_rpm_reload;
    uint8_t drive_snapshot_delta[2], fault_options, kicker_baseline_limit;
    uint8_t learning_error_limit, learning_count_limit, reset_speed;
    uint8_t output_options, prestart_coolant_minimum, park_target;
    uint8_t default_integral[2], default_ac_warm, default_ac_cold, default_coolant, default_baseline;
    uint8_t start_hold_curve[2][17], start_cold_curve[2][17], start_rpm_curve[17];
    uint8_t start_flow, start_rpm_hold;
    uint8_t gear_flow[2], gear_hold[2], gear_delay[2], gear_coolant;
    uint8_t gear_cold_hold[2], gear_cold_delay[2];
    uint8_t ac_transition_gain[2], ac_transition_minimum[2], ac_transition_maximum[2];
    uint8_t ac_transition_hold[2], ac_transition_delay[2];
    PcmOffsetCurve ac_temperature, baro;
    uint8_t steering_flow, steering_delay, error_gain, error_deadband[4];
    uint8_t closed_throttle, closed_speed, closed_delay, stall_flow[4], stall_hold[2];
    uint8_t integral_curve[4][12], proportional_curve[10][12], derivative_curve[17];
    uint8_t proportional_speed_entry, proportional_speed_exit, proportional_error_limit;
    uint8_t derivative_fast_gain, derivative_slow_gain;
    uint8_t reconcile_coolant, reconcile_flow[2], reconcile_error, reconcile_phase;
    PcmScaledCurve enrichment_curve;
    uint8_t enrichment_throttle, enrichment_flow, dfco_bias, dfco_curve[17];
    uint16_t pe_flow_limit;
    uint8_t kicker_flow_subtract, kicker_flow_gain, position_curve[18];
    uint8_t step_battery_minimum; /* 4EB6; comparison is strictly greater. */
} PcmIacCalibration;

typedef struct {
    uint8_t map_default, map_throttle_gain, map_normal_gain, map_transient_gain;
    PcmCappedCurve map_bias; /* Cap RPM>>1 before subtracting fixed offset16. */
    uint8_t brake_delay;
} PcmIoCalibration;

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
    const PcmTransmissionCalibration *transmission;
    const PcmIacCalibration *iac;
    const PcmIoCalibration *io;
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
    volatile bool fuel_running;        /* RAM004F.4 */
    volatile bool spark_running;       /* RAM004F.7 */
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
    volatile bool deceleration_fuel_cut; /* RAM0046.3 */
} PcmRuntime;

typedef struct {
    volatile uint8_t rpm_coordinate;    /* RAM0062, not engineering RPM */
    volatile bool latch_inhibited;     /* RAM0044.4, distinct from0051.3 */
    volatile bool pending;             /* RAM0050.5: one bit, never a count */
    volatile bool consumed;            /* RAM0050.2, set when spark consumes a reference */
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
    volatile uint8_t rpm_fraction;      /* RAM0064, low byte paired with rpm_high0063 */
    volatile uint8_t iac_desired_speed, idle_derivative; /* RAM0857,006C, explicit IAC inputs */
    volatile bool idle_negative;       /* RAM0053.0; unsigned target/RPM borrow */
    volatile uint8_t transient_target, transient_error, transient_correction; /* 0837,083A,083B */
    volatile uint16_t transient_filtered; /* RAM0838 */
    volatile bool recovery_active;     /* RAM0051.5 */
    volatile uint8_t decel_retard;      /* RAM0208 */
    volatile uint16_t startup_recovery_gain; /* RAM01F2, one shared startup/decel word */
    volatile bool override_request, override_active; /* RAM0036.5,0053.4 */
    volatile uint8_t service_flags, service_amount; /* RAM0395,0398 */
    volatile uint16_t command_latched;  /* RAM01F0, common post-service latch */
    volatile uint8_t map_filtered, barometric_high, normalized_load_divisor; /* 01C6,02F4,01CE */
    volatile uint16_t density;          /* RAM0257, upstream normalized-load numerator */
    volatile uint8_t normalized_load, map_fault_count; /* 01CF,0229 */
    volatile bool map_fault, first_reference; /* RAM0018.4,0044.3 */
    volatile bool startup_gain_enabled, startup_gain_complete, run_transition; /* 004F.6,0051.6,0004.3 */
    volatile uint8_t fuel_run_count, spark_run_count, missing_reference_count; /* 0211,0210,0202 */
    volatile uint16_t reference_age, adaptive_period, period_basis; /* 0260,01EA,005F */
    volatile uint16_t rpm_raw, rpm_monitor_filtered; /* RAM083D,028E */
    volatile uint8_t rpm_monitor_previous, rpm_monitor_delta; /* RAM028C,028D */
    volatile uint16_t period, previous_period, reference_term, period_correction; /* 01E8,01E6,083F,01EC */
    volatile uint8_t battery_sample;    /* RAM00A7; separate from reference.battery0055 */
    volatile bool command_negative, output_request; /* RAM004F.0,004B.4 */
    volatile uint8_t output_latency;    /* RAM0201 */
    volatile bool bypass_qualified, bypass_fault_latched, est_fault; /* 0044.6,0044.7,0019.5 */
    volatile bool bypass_supervision, service_bypass; /* 0004.7,0391.3, upstream inputs */
    volatile uint16_t bypass_baseline; /* RAM0205, saved 3FCA sample */
    volatile uint8_t bypass_count;     /* RAM022C, wrapping byte */
    uint8_t extension_magnitude;        /* C180F dependency argument/result, no factory RAM address */
} PcmSpark;

typedef struct {
    volatile uint8_t selected_gear, output_shadow; /* 00D9,004C */
    volatile uint8_t inhibit_flags, fault_flags_primary, fault_flags_secondary; /* 0099,001C,001D */
    volatile bool driver_inhibit;      /* 0086.0; shares its byte with profiling0086.6 */
    volatile uint8_t output_fault_flags; /* 008E */
    volatile uint8_t current_service_enable, current_service_value; /* 039A,039B, bit6 */
    volatile uint8_t tcc_flags, tcc_state; /* 008A,008B */
    volatile uint16_t tcc_command, tcc_lower_limit; /* 0126,012B */
} PcmTransmission;

typedef struct {
    volatile uint16_t no_ac, ac, cold, bound;
    volatile uint8_t no_ac_snapshot, ac_snapshot;
} PcmIacBank;
typedef struct {
    /* Context carries0036 bitsDF only. Bit5 remains spark.override_request. */
    volatile uint8_t context, kicker_flags, transfer_flags, learning_flags, state_flags; /* 0036..0039,0009 */
    volatile bool low_battery, learning_fault, kicker_request, service_kicker; /* 003E.2,0018.3,004B.7,038F.6 */
    PcmIacBank bank[2];                /* 0=park029D..02A6; 1=drive02A7..02B0 */
    volatile uint16_t proposed[2][2], cold_proposed[2]; /* 088F/0891/0895/0897;0893/0899 */
    volatile uint8_t baseline_on, baseline_off, tps_zero_high, tps_zero_low; /* 02B1,02B2,02F6,02F7 */
    volatile uint8_t coolant_index, runtime_high, blm_cell_index, blm_value; /* 0283,0232,0247,0248 */
    volatile uint8_t rpm_error, blm_count, startup_rpm_adder, slewed_base; /* 0858,085B,085C,085F */
    volatile uint16_t rpm_error_filtered; /* 0859 */
    volatile uint8_t switch_offset, switch_delay, hold[2], stall_threshold, selected_snapshot; /* 0860,0861,0866/67,0868,086A */
    volatile uint8_t cold_delay, ac_adder, ac_hold, ac_divider; /* 0875..0878 */
    volatile uint8_t dfco_adder, dfco_divider, kicker_timer; /* 0887,0888,088D */
    volatile uint16_t follower, follower_filtered; /* 0880,0882 */
    volatile uint8_t follower_hold, follower_closed_threshold, follower_age; /* 0884..0886 */
    volatile uint8_t starting_coolant, switch_adder, switch_hold; /* 0282,087B,087C */
    volatile uint8_t startup_flow, startup_flow_divider, startup_rpm_divider, startup_rpm_hold; /* 086B/6C,085D/5E */
    volatile uint8_t learning_count, position, target; /* 088E,0007,0008 */
    volatile bool startup_cancel, kicker_fault, input_fault; /* 003F.6,0018.2,0017.7 */
    volatile bool park_neutral, ac_request, service_reset, service_kicker_value; /* 0041.5,0052.5,0391.5,0390.6 */
    volatile uint8_t gear_status, input_shadow, service_value; /* 00A2,004D,0396 */
    volatile uint8_t qualification_delay, stall_hold, proportional, derivative; /* 0864,0869,086D,0870 */
    volatile uint8_t gear_adder, gear_hold, enrichment; /* 0879,087A,087F */
    volatile uint16_t selected_integral, selected_cold, selected_bound, derivative_filtered; /* 0862,0871,0873,086E */
    volatile uint16_t composite_flow, pre_baro_flow, airflow; /* 087D,0889,088B */
    volatile uint8_t step_control; /* 000A: direction0, ring0C, enable10; other bits retained. */
} PcmIac;

typedef struct {
    volatile uint8_t output_context; /* 004B bits6F;10/80 belong to spark/IAC. */
    volatile uint8_t auxiliary_output; /* 004E */
    volatile uint16_t status_context; /* 0073/74 bitsBFFF;4000 belongs to REF.extra_request. */
    volatile uint16_t map_filter; /* 01C3/4 */
    volatile bool map_transient, ac_mirror, brake_active; /* 0047.0,0041.4,009C.0 */
    volatile uint8_t vss_changes, brake_count; /* 080C,00FB */
    volatile uint16_t vss_timestamp; /* 080D */
} PcmIo;

typedef struct Pcm {
    const PcmPlatform *platform; /* immutable bindings can live in ROM */
    const PcmCalibration *calibration;
    PcmScheduler scheduler;
    PcmRuntime runtime;
    PcmReference reference;
    PcmKnock knock;
    PcmSpark spark;
    PcmTransmission transmission;
    PcmIac iac;
    PcmIo io;
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
