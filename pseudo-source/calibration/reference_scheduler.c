#include "calibration.h"
/* Source defaults, not a binary storage format. Factory 495D contains000A. */
const PcmCalibration pcm_reference_scheduler_calibration = {
    .format_version = 1,
    .recurring_compare_counts = 819,
    .first_compare_counts = 8,
    .run_counter_clear_threshold = 10,
    .initial_phase = 0x0e
};
