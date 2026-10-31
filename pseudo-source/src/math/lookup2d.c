#include "reference_math.h"
static uint8_t interpolate(uint8_t first, uint8_t second, uint8_t fraction)
{
    uint8_t difference = first > second ? (uint8_t)(first - second) : (uint8_t)(second - first);
    uint8_t step = (uint8_t)(((uint16_t)difference * fraction + 128u) >> 8);
    return first > second ? (uint8_t)(first - step) : (uint8_t)(first + step);
}
/* F4DE..F54F: rounded columns then rounded rows. F501 uses ABX's byte B,
 * so row-index*stride wraps before adding the column and the second stride. */
PcmStatus pcm_lookup2d(uint8_t row, uint8_t column, const PcmTable2D *table, uint8_t *result)
{
    if (table == NULL || table->values == NULL || result == NULL) return PCM_BAD_CONFIGURATION;
    row = row >= table->row_offset ? (uint8_t)(row - table->row_offset) : 0;
    column = column >= table->column_offset ? (uint8_t)(column - table->column_offset) : 0;
    uint16_t first = (uint16_t)(uint8_t)((row >> 4) * table->stride) + (column >> 4);
    uint16_t second = (uint16_t)(first + table->stride);
    if (second + 1u >= table->length) return PCM_BAD_CONFIGURATION;
    uint8_t below = interpolate(table->values[second], table->values[second + 1u], (uint8_t)(column << 4));
    uint8_t above = interpolate(table->values[first], table->values[first + 1u], (uint8_t)(column << 4));
    *result = interpolate(above, below, (uint8_t)(row << 4));
    return PCM_OK;
}
