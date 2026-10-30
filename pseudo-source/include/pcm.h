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
    PCM_SLOT_04, PCM_SLOT_05, PCM_SLOT_06, PCM_SLOT_07,
    PCM_SLOT_08, PCM_SLOT_09, PCM_SLOT_0A, PCM_SLOT_0B,
    PCM_SLOT_0C, PCM_SLOT_0D, PCM_SLOT_0E, PCM_SLOT_0F,
    PCM_REFERENCE_BODY, PCM_OC1_BODY, PCM_SCI_BODY,
    PCM_RESET_CPU, PCM_RESET_OUTPUTS, PCM_RESET_RAM,
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
    /* Must establish the documented entry-stack precondition. Target stack
     * guard/recovery is deliberately delegated, not simulated with C SP. */
    PcmStatus (*check_stack)(void *, bool busy);
    PcmDependency task[PCM_TASK_COUNT];
} PcmPlatform;

typedef struct {
    uint16_t format_version;
    uint16_t recurring_compare_counts;
    uint16_t first_compare_counts;
    uint16_t run_counter_clear_threshold;
    uint8_t initial_phase;
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
} PcmRuntime;

typedef struct Pcm {
    const PcmPlatform *platform; /* immutable bindings can live in ROM */
    const PcmCalibration *calibration;
    PcmScheduler scheduler;
    PcmRuntime runtime;
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
