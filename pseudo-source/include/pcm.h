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
    PCM_EGR_DEMAND, PCM_VSS_FILTER, PCM_IAC_EXTENSION, PCM_AFR_EXTENSION, PCM_TRANSMISSION_INPUT_PREFIX, PCM_TASK_COUNT
} PcmTask;

struct Pcm;
typedef PcmStatus (*PcmRoutine)(struct Pcm *);
typedef PcmStatus (*PcmDependency)(struct Pcm *, PcmTask);
typedef struct {
    void *context;
    /* ALDL also uses the logical CPU address space. Providers must bind
     * non-serial RAM to its named Pcm owners, and supply ROM/device semantics;
     * these callbacks never imply that native C layout equals factory RAM. */
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
    uint8_t shift_ratio[4], shift_rpm[4], shift_throttle_gain[4]; /* 5113..511E */
    uint8_t shift_coolant, shift_throttle[2], shift_rpm_max, shift_reload[2]; /* 511F..5124 */
    uint8_t shift_curves[55];          /* 5125..515B: four overlapping RPM views and baro knots */
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
    uint8_t map_hold_reload, map_rpm_delta_limit, vss_gain; /* 4139/3A,4E8E */
} PcmIoCalibration;

typedef struct {
    uint8_t throttle_limit[2], entry_delay, exit_delay, throttle_delay; /* 4010..4014 */
    uint8_t rpm_count_limit, rpm_release_delay, rpm_limit[2], running_rpm_limit; /* 4015..4019 */
    uint8_t coolant_limit[2], speed_limit[2], throttle_release[2]; /* 401A..401F */
    uint16_t throttle_count_limit, runtime_minimum; /* 4020,4022 */
} PcmAcCalibration;

typedef struct {
    uint8_t coolant_trim[17], coolant_factor[9], coolant_load[14], coolant_idle[17];
    uint8_t low_coolant_limit, low_coolant_subtract; /* 48E3,48E8 */
    PcmCappedCurve density;            /* 475F header; cap before fixed80 subtraction */
} PcmEnvironmentCalibration;

typedef struct {
    uint16_t synchronous_minimum, synchronous_replacement; /* 496D,496F */
    uint8_t injection_delay_gain, offset[17]; /* 4973,4B05..4B15 */
} PcmFuelCalibration;

typedef struct {
    uint8_t throttle_gain, throttle_default, throttle_zero_minimum, throttle_zero_gain;
    uint16_t coolant_runtime_limit, mat_runtime_limit;
    uint8_t coolant_default_late, coolant_default_early, coolant_table[2][256];
    uint8_t mat_options, mat_low_threshold, mat_low_delay, mat_high_threshold, mat_high_delay;
    uint8_t mat_speed_limit, mat_default, mat_curve[17];
    uint8_t baro_options, baro_rpm_upper, baro_rpm_lower, baro_throttle_minimum;
    uint8_t baro_throttle_delta, baro_gain, baro_coolant_minimum;
    PcmTable2D baro_correction, ve_open, ve_idle;
    uint8_t baro_ae[4], baro_pe_throttle[4], baro_pe_rpm[4], baro_load[4];
    uint8_t charge_weight[17], charge_curve[17], ve_speed_limit, ve_integrator_limit;
    uint16_t injector_flow;
    uint8_t cylinder_volume;
} PcmAirCalibration;

typedef struct {
    uint16_t authorization_minimum, authorization_maximum, crank_base;
    uint8_t oxygen_minimum, oxygen_maximum, oxygen_idle_gain, oxygen_gain[17];
    uint8_t map_threshold[2], map_closed_throttle, map_double_throttle;
    uint8_t tps_threshold, tps_speed_gain, tps_speed_limit, history_reload, history_gain;
    PcmScaledCurve ae_map, ae_base, startup_spark, startup_spark_delay, startup_spark_gain, crank_tps;
    PcmCappedCurve ae_rpm, pe_upper, pe_exit, pe_entry;
    uint8_t tps_curve[17], ae_coolant[17], ae_mat[17], ae_map_gain[17];
    uint8_t startup_afr[17], startup_interval[17], startup_air[5], startup_ref[17], startup_decrement[17], spark_air[5];
    uint8_t startup_hold, startup_afr_gain, startup_rpm_delta, startup_effort;
    uint8_t startup_coolant_limit, startup_afr_limit, startup_park_hold;
    uint8_t crank_age, period_scale, crank_coolant[17], crank_normal[9], crank_hot[9], crank_baro[11], crank_battery[17];
    PcmTable2D open_afr;
    uint8_t open_mode, stoich, open_coolant, afr_filter_gain, idle_speed, idle_throttle;
    uint8_t idle_entry_delay, idle_apply_delay, idle_coolant, idle_integrator_limit;
    uint16_t idle_runtime;
    uint8_t hotstart_subtract, warm_coolant[2], warm_duration, warm_drive_subtract, warm_park_subtract;
    uint8_t afr_maximum, afr_alternate_maximum, enrichment_age, enrichment_coolant;
    uint8_t pe_permission_speed, pe_permission_throttle, pe_permission_delay;
    uint8_t pe_rpm_delta, pe_coolant[2], pe_hysteresis, pe_rpm, pe_exit_delay, pe_gain_delay, pe_gain_step;
    uint8_t pe_cold_coolant, pe_time, pe_warm_coolant, pe_cold_rpm, pe_cold_speed, pe_cold_subtract, pe_part_throttle;
    uint16_t pe_vehicle_change;
    uint8_t pe_target[17], output_rich_limit[17];
} PcmMixtureCalibration;

typedef struct {
    uint8_t activity[8], airflow_gain, idle_thresholds[2], idle_center, alternate_interval, direction_band;
    uint8_t activity_age_limit, starting_coolant[2], warmup_time[3], closed_coolant, warmup_afr;
    uint8_t learning_coolant, stoich, learning_vacuum, learning_load[2], learning_rpm;
    uint8_t control_load, control_rpm_lower, control_rpm_upper, control_speed;
    uint8_t positive_error_gain, idle_error_gain, oxygen[4][10], error_curve[14];
    uint8_t idle_base_delay, idle_coefficient[3], idle_interval[2], base_delay[17], error_delay[14], interval_gain[14];
    uint8_t integrator_deadband, integrator_minimum, integrator_maximum, proportional_cap, window_width;
    uint8_t rpm_bins[3], load_bins[3], rpm_margin, load_margin, special_cells, idle_throttle, idle_speed;
    uint8_t blm_minimum[2], blm_maximum, boot_maximum, boot_minimum, learning_error[2];
    uint8_t transition_positive, transition_negative, transition_integrator_low, transition_integrator_high;
    uint8_t learning_delay, learning_step, derivative_load, derivative_throttle, derivative_speed, derivative_coolant;
    uint8_t derivative_bounds[2], battery[17];
    PcmTable2D proportional, baro;
} PcmFeedbackCalibration;

typedef struct {
    uint8_t qualification_reload, qualification_speed, qualification_throttle, qualification_rpm[2];
    uint8_t cut_delay, cut_minimum_rpm, cut_rpm[4], cut_speed[2];
    uint8_t transition_enrichment, ac_enrichment, acceleration_hold;
    uint8_t decel_coolant, decel_rpm_change, decel_map_change, decel_rpm_adder;
    uint8_t decel_load_entry, decel_load_retained, decel_speed[2], decel_delay, decel_active_reload, reduction_step;
    uint16_t recovery_fuel;
    PcmCappedCurve decel_throttle;
    uint8_t throttle_drop_minimum, load_drop_minimum, slow_enleanment_gain, enleanment_speed;
    uint8_t enleanment_load[12], enleanment_throttle[17];
    uint16_t sync_threshold[2]; /* entry492C, retained492A */
    uint8_t sync_load[2], sync_rpm[2]; /*4930/492E,4931/492F */
    uint8_t cpi_delay;
    uint16_t packet_maximum, packet_minimum;
} PcmDeliveryCalibration;

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
    const PcmAcCalibration *ac;
    const PcmEnvironmentCalibration *environment;
    const PcmFuelCalibration *fuel;
    const PcmAirCalibration *air;
    const PcmMixtureCalibration *mixture;
    const PcmFeedbackCalibration *feedback;
    const PcmDeliveryCalibration *delivery;
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
    volatile bool engine_service;      /* RAM003B.4 */
    volatile bool transmission_service; /* RAM003B.3 */
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
    volatile bool diagnostic_switch;   /* RAM0050.4, produced by resident CB15 inputs */
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
    volatile uint8_t current_service_enable, current_service_value; /* 039A,039B; output and solenoid masks. */
    volatile uint8_t service_gear, service_tcc, service_pressure, service_state, adaptive_flags; /*0103,010A,0111,0118,011A */
    volatile uint8_t diagnostic_status[2]; /*0130/0131, packed by F64E */
    volatile uint8_t tcc_flags, tcc_state; /* 008A,008B */
    volatile uint16_t tcc_command, tcc_lower_limit; /* 0126,012B */
    volatile uint8_t range_context, shift_gear, shift_hold, shift_ratio; /* 0089,0845/46/4B */
    volatile bool shift_lamp, shift_service_enable, shift_service_value; /* 0053.2,038F.0,0390.0 */
    volatile uint16_t shift_counter, shift_delta; /* 0847,0849 */
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
    volatile uint8_t map_context, map_hold, map_previous_rpm, coolant_context; /* 0047 bitsFE,01C5,0065,003E bitsFB */
    volatile uint16_t vss_previous, vss_raw; /* 080F,0812 */
    volatile uint8_t vss_age, vehicle_speed_fraction; /* 0811,0285; high byte remains spark owner */
    volatile uint8_t diagnostic_sample; /* 082F */
    volatile bool diagnostic_warm, ac_rpm_inhibit; /* 0050.3,0052.4 */
    volatile uint8_t ac_entry, ac_exit, ac_rpm_count, ac_release_count, ac_throttle_delay; /* 0830..33,0836 */
    volatile uint16_t ac_throttle_count; /* 0834 */
    volatile uint8_t environmental_trim, environmental_factor, environmental_load;
    volatile uint8_t environmental_idle, environmental_density; /* 01E5,0243,0272,01CB,01BB */
    volatile uint8_t raw_coolant, auxiliary_sample, auxiliary_reference; /* 082D,01A1,00A5 */
    volatile uint8_t coolant_conversion, mat_raw, mat_display; /* 00A8,0230,0855 */
    volatile uint8_t mat_low_count, mat_high_count; /* 021D,021E */
    volatile bool mat_low_fault, mat_high_fault; /* 0017.6,0017.4; IAC owns0017.7 */
    volatile uint8_t barometric_sample, barometric_fraction; /* 02F3,02F5; high remains spark owner */
    volatile uint8_t tps_ae_factor, pe_throttle_threshold, pe_rpm_threshold; /* 01E4,01E3,01CD */
} PcmIo;

typedef struct {
    volatile uint16_t corrected_pulse; /* RAM024E, before delivery shaping */
    volatile bool short_pulse;        /* RAM003F.7; extra_guard owns bit4 */
    volatile uint8_t raw_throttle, raw_oxygen, measured_current; /* 00A6,01D5,014E */
    volatile uint8_t normalized_throttle, integrator, volumetric_efficiency, commanded_afr;
    /* 01A6,020F,0231,024A */
    volatile bool throttle_fault, open_ve, ve_reset_request; /* 0098.0,004F.3,004F.5 */
    volatile uint16_t throttle_decel_filter; /* 01DE/DF; independent of previous TPS01DA */
    volatile uint16_t charge_temperature, displaced, air_charge; /* 0236,0238,0234 */
    volatile uint8_t air_rate_fraction; /* 0233; high byte remains iac.runtime_high0232 */
    volatile bool authorized, map_acceleration, tps_acceleration, pe_permission, pe_full_gain;
    /* 003D.1,0005.7,0005.6,003D.0,003F.5; PE active remains runtime owner. */
    volatile bool idle_afr_ready, alternate_afr_limit, output_rich_cap; /* 0050.1,0072.6,0052.6 */
    volatile uint8_t startup_context, startup_previous_rpm; /* 003F low nibble,0066 */
    volatile uint16_t authorization_capture, oxygen_filtered, map_history, tps_history; /* 0851,01D2,01C7,01DC */
    volatile uint8_t oxygen_coordinate, map_delta, map_ae, tps_ae, base_ae_gain, tps_ae_gain, map_ae_gain;
    /* 027B,01CA,023E,023F,0242,023C,023D */
    volatile uint8_t history_count, startup_afr, startup_hold, startup_spark_delay, startup_spark_gain;
    /* 0240,02C8,02CA,02CC,01FF; spark startup adder and REF enrichment remain existing owners. */
    volatile uint8_t startup_park_hold, startup_interval, startup_spark_interval; /* 027D,0270,0200 */
    volatile uint16_t afr_filtered; /* 0264 */
    volatile uint8_t afr_filter_count, idle_afr_count, warm_afr_count, published_afr; /* 0266,0271,082C,024B */
    volatile uint8_t pe_permission_count, pe_upper_throttle, pe_exit_step, pe_entry_throttle, pe_previous_throttle;
    /* 0263,01E0,01E1,01E2,01DB */
    volatile uint8_t pe_gain_count, pe_target_count, pe_exit_count, service_afr; /* 0277,0269,0276,0397 */
    volatile uint16_t pe_vehicle_change; /* 0818; BLM tail produces this retained magnitude. */
    volatile bool oxygen_activity, oxygen_warmed, warmup_control, closed_seen; /* 0004.0/.1,0052.7,0046.7 */
    volatile bool oxygen_changed, oxygen_error_positive, oxygen_notification; /* 0043.4,0046.1,0071.2 */
    volatile bool fuel_activity, enrichment_entry, asynchronous_active; /* 0044.1,006E.3,006E.0 */
    volatile bool blm_transition, blm_cell_changed, blm_invalid, blm_closed_throttle, decel_enleanment;
    /* 003D.2/.3,0046.6,0052.2,003D.4 */
    volatile bool oxygen_fault_a, oxygen_fault_b, oxygen_idle_fault, alternate_interval;
    /* 0019.2/.3,0018.5,0070.2; MAP fault0018.4 remains spark.map_fault. */
    volatile bool oxygen_service, oxygen_service_value; /* 0391.0,0392.0 */
    volatile uint8_t module_state, oxygen_age, previous_oxygen, oxygen_changes, oxygen_direction_age;
    /* 0801,0241,01D4,0275,027C */
    volatile uint8_t oxygen_interval, oxygen_center, oxygen_upper, oxygen_lower; /* 026B..026E */
    volatile uint8_t proportional, feedback_encoded, oxygen_error, interval_snapshot, idle_oxygen_interval, integrator_delay;
    /* 027A,026F,0280,0281,0262,025F */
    volatile uint8_t blm_previous, blm_learning_count, blm_interval_count, blm_cells[21]; /* 0249,0273/74,02B3..02C7 */
    volatile uint16_t previous_vehicle_speed, egr_subtract; /* 081A,0252 */
    volatile uint8_t egr_fraction_low; /* 01B3; high remains spark.egr_fraction_high. */
    volatile bool qualification_latch, cut_active, acceleration_active, async_pending;
    /* 0053.3,0046.4,003D.6/.7 */
    volatile bool ac_enrichment_seen, decel_throttle_latch, async_suppressed; /*0041.3,0053.1,0046.0 */
    volatile uint8_t qualification_count, cut_count, acceleration_hold; /*084D,026A,081D */
    volatile uint8_t reduction_factor, decel_timer, decel_delay, throttle_drop; /*0244..46,082B */
    volatile uint16_t acceleration_reservoir, async_quotient; /*023A,025C/5D */
    volatile uint8_t async_accumulator_high, async_remainder; /*0259,025E */
    volatile uint16_t async_accumulator_fraction; /*025A/5B; word0259 spans high + fraction high. */
    /* Async-route bit003E.4 remains in io.coolant_context, not duplicated. */
} PcmFuel;

typedef struct {
    volatile uint8_t sessions, clear_edges; /*0042,0045; preserve unrelated bits. */
    volatile bool clear_engine, clear_transmission, deferred, busy, companion_pending; /*003B.1/.0/.5/.6/.7 */
    volatile uint8_t count, checksum, last_id, length, companion, receive_age; /*0360/61,0364..67 */
    volatile uint16_t descriptor, service_age, service_expiry; /*0362,0368,036A */
    volatile uint8_t receive[34], engine_command, transmission_command; /*036C..038D,038E,0399 */
} PcmSerial;

typedef struct {
    volatile uint8_t factory_flags; /*0001, factory callback-arm byte; not scheduler busy. */
    volatile uint8_t diagnostic_checksum; /*0015, negative sum of0014..000B */
    volatile uint8_t startup_counter; /*0049, reset seed20 */
} PcmSystem;

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
    PcmFuel fuel;
    PcmSerial serial;
    PcmSystem system;
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
