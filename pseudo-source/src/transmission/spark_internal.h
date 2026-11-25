#ifndef PCM_TRANSMISSION_SPARK_INTERNAL_H
#define PCM_TRANSMISSION_SPARK_INTERNAL_H
#include "../emissions/egr_internal.h"

/* $DA8D and $DB15 supply the same row and column to the factory $F4DE lookup. */
static inline PcmStatus transmission_retard_surface(Pcm *pcm, uint16_t table, uint8_t *retard)
{
    uint8_t column = pcm->spark.load_coordinate;
    uint8_t row = pcm->spark.rpm_low_coordinate;
    if (row > 0x40u) {
        uint8_t high = pcm->reference.rpm_coordinate;
        row = high > 0xefu ? 255u : (uint8_t)(high + 16u);
    }
    return egr_surface(pcm, row, column, table, retard);
}
#endif
