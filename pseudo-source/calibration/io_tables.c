#include "calibration.h"
static const uint8_t map_bias_knots[5]={0x70,0x55,0x33,0x23,0x00};
const PcmIoCalibration pcm_reference_io_calibration={
    .map_default=0xda, /* 4E68 */
    .map_throttle_gain=0x80, /* 4E69 */
    .map_normal_gain=0x40, /* 4137 */
    .map_transient_gain=0xf0, /* 4138 */
    .brake_delay=0x04, /* 5D06 */
    .map_bias={0x40,5,map_bias_knots}, /* 4E6A..4E6F */
};
