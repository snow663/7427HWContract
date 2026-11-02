#define B(a,m) {a,8,0,1,offsetof(Pcm,m)}
#define W(a,m) {a,16,0,1,offsetof(Pcm,m)}
#define F(a,b,m) {a,0,b,1,offsetof(Pcm,m)}
static const Mapping delivery_state_map[] = {
F(0x53,8,fuel.qualification_latch),F(0x46,0x10,fuel.cut_active),F(0x3d,0x40,fuel.acceleration_active),F(0x3d,0x80,fuel.async_pending),
F(0x41,8,fuel.ac_enrichment_seen),F(0x53,2,fuel.decel_throttle_latch),F(0x46,1,fuel.async_suppressed),
B(0x84d,fuel.qualification_count),B(0x26a,fuel.cut_count),B(0x81d,fuel.acceleration_hold),
B(0x244,fuel.reduction_factor),B(0x245,fuel.decel_timer),B(0x246,fuel.decel_delay),B(0x82b,fuel.throttle_drop),
W(0x23a,fuel.acceleration_reservoir),W(0x25c,fuel.async_quotient),B(0x259,fuel.async_accumulator_high),W(0x25a,fuel.async_accumulator_fraction),B(0x25e,fuel.async_remainder),
W(0x812,io.vss_raw),B(0x99,transmission.inhibit_flags),B(0x87f,iac.enrichment),
};
#undef B
#undef W
#undef F
#define B(a,m) {a,8,0,1,offsetof(PcmDeliveryCalibration,m)}
#define W(a,m) {a,16,0,1,offsetof(PcmDeliveryCalibration,m)}
#define A(a,n,m) {a,8,0,n,offsetof(PcmDeliveryCalibration,m)}
static const Mapping delivery_cal_map[] = {
    B(0x5155,qualification_reload),
    B(0x5156,qualification_speed),
    B(0x5159,qualification_throttle),
    B(0x4965,cut_delay),
    B(0x4966,cut_minimum_rpm),
    B(0x48c6,transition_enrichment),
    B(0x48c7,ac_enrichment),
    B(0x48ca,acceleration_hold),
    B(0x4944,decel_coolant),
    B(0x4945,decel_rpm_change),
    B(0x4946,decel_map_change),
    B(0x493a,decel_rpm_adder),
    B(0x493d,decel_load_entry),
    B(0x493e,decel_load_retained),
    W(0x493f,recovery_fuel),
    B(0x4941,decel_delay),
    B(0x4942,decel_active_reload),
    B(0x4943,reduction_step),
    B(0x4936,throttle_drop_minimum),
    B(0x4937,load_drop_minimum),
    B(0x4938,slow_enleanment_gain),
    B(0x4939,enleanment_speed),
    B(0x4974,cpi_delay),
    W(0x4932,packet_maximum),
    W(0x4934,packet_minimum),
    A(0x5157,2,qualification_rpm),
    A(0x4967,4,cut_rpm),
    A(0x496b,2,cut_speed),
    A(0x493b,2,decel_speed),
    A(0x4b20,12,enleanment_load),
    A(0x4b2b,17,enleanment_throttle),
    W(0x492c,sync_threshold[0]),B(0x4930,sync_load[0]),B(0x4931,sync_rpm[0]),
    W(0x492a,sync_threshold[1]),B(0x492e,sync_load[1]),B(0x492f,sync_rpm[1]),
};
#undef B
#undef W
#undef A
static const uint8_t delivery_curve_backing[17] = { 0x00,0x04,0x04,0x07,0x08,0x09,0x09,0x09,0x1e,0x1e,0x1e,0x1e,0x1e,0x1e,0x1e,0x1e,0x1e };
