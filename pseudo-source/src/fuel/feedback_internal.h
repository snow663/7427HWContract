#ifndef PCM_FEEDBACK_INTERNAL_H
#define PCM_FEEDBACK_INTERNAL_H
#include "mixture_internal.h"
#define FB_CAL() \
    if (pcm->calibration == NULL || pcm->calibration->feedback == NULL) return PCM_BAD_CONFIGURATION; \
    const PcmFeedbackCalibration *cal = pcm->calibration->feedback
#define FB_RUN(call) MIX_RUN(call)
#endif
