#include "calibration.h"
static const uint8_t decel_throttle[9] = { 0x00,0x04,0x04,0x07,0x08,0x09,0x09,0x09,0x1e };
const PcmDeliveryCalibration pcm_reference_delivery_calibration = {
    .qualification_reload = 0x02, /*5155*/
    .qualification_speed = 0x10, /*5156*/
    .qualification_throttle = 0xc0, /*5159*/
    .cut_delay = 0x78, /*4965*/
    .cut_minimum_rpm = 0x30, /*4966*/
    .transition_enrichment = 0x21, /*48C6*/
    .ac_enrichment = 0x00, /*48C7*/
    .acceleration_hold = 0x50, /*48CA*/
    .decel_coolant = 0x98, /*4944*/
    .decel_rpm_change = 0x08, /*4945*/
    .decel_map_change = 0x20, /*4946*/
    .decel_rpm_adder = 0x14, /*493A*/
    .decel_load_entry = 0x0e, /*493D*/
    .decel_load_retained = 0x60, /*493E*/
    .recovery_fuel = 0x08ff, /*493F*/
    .decel_delay = 0x10, /*4941*/
    .decel_active_reload = 0x80, /*4942*/
    .reduction_step = 0xa0, /*4943*/
    .throttle_drop_minimum = 0x03, /*4936*/
    .load_drop_minimum = 0x08, /*4937*/
    .slow_enleanment_gain = 0x80, /*4938*/
    .enleanment_speed = 0x06, /*4939*/
    .cpi_delay = 0x00, /*4974*/
    .packet_maximum = 0x0312, /*4932*/
    .packet_minimum = 0x005c, /*4934*/
    .qualification_rpm = { 0xa0,0x98 }, /*5157*/
    .cut_rpm = { 0xc0,0xbe,0xc0,0xbe }, /*4967*/
    .cut_speed = { 0x62,0x60 }, /*496B*/
    .decel_speed = { 0x0a,0x07 }, /*493B*/
    .enleanment_load = { 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00 }, /*4B20*/
    .enleanment_throttle = { 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00 }, /*4B2B*/
    .sync_threshold[0] = 0x0014, .sync_load[0] = 0xfe, .sync_rpm[0] = 0xfe,

    .sync_threshold[1] = 0x0021, .sync_load[1] = 0xff, .sync_rpm[1] = 0xff,

    .decel_throttle = { 0x90,9,decel_throttle }, /*4C94, cap before offset32*/
};
