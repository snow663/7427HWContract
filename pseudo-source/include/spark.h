#ifndef PSEUDO_SOURCE_SPARK_H
#define PSEUDO_SOURCE_SPARK_H
#include "pcm.h"
PcmStatus pcm_spark_base(Pcm *);
PcmStatus pcm_spark_coolant(Pcm *);
PcmStatus pcm_spark_altitude(Pcm *);
PcmStatus pcm_spark_egr(Pcm *);
PcmStatus pcm_spark_sum(Pcm *);
PcmStatus pcm_spark_mat_effect(Pcm *);
PcmStatus pcm_spark_mat(Pcm *);
PcmStatus pcm_spark_pe(Pcm *);
PcmStatus pcm_spark_auxiliary(Pcm *);
PcmStatus pcm_spark_terms(Pcm *);
PcmStatus pcm_spark_idle(Pcm *);
PcmStatus pcm_spark_transient(Pcm *);
PcmStatus pcm_spark_decel(Pcm *);
PcmStatus pcm_spark_modifiers(Pcm *);
PcmStatus pcm_spark_composite(Pcm *);
#endif
