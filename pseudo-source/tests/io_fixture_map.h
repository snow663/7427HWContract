/* Test-only field/address mapping; status4000 and output90 retain existing owners. */
#define B(a,m) {a,8,0,1,offsetof(Pcm,m)}
#define W(a,m) {a,16,0,1,offsetof(Pcm,m)}
#define F(a,b,m) {a,0,b,1,offsetof(Pcm,m)}
static const Mapping io_state_map[]={
    {0x4b,7,0x6f,1,offsetof(Pcm,io.output_context)},
    B(0x4e,io.auxiliary_output),F(0x72,0x80,runtime.service_output_mirror),
    {0x73,15,0xbf,1,offsetof(Pcm,io.status_context)},
    F(0x73,0x40,reference.extra_request),
    W(0x6a,reference.load_event),W(0x1c3,io.map_filter),F(0x47,1,io.map_transient),F(0x41,0x10,io.ac_mirror),
    F(0x9c,1,io.brake_active),B(0xfb,io.brake_count),B(0x80c,io.vss_changes),W(0x80d,io.vss_timestamp)
};
#undef B
#undef W
#undef F
#define C(a,m) {a,8,0,1,offsetof(PcmIoCalibration,m)}
static const Mapping io_cal_map[]={
    C(0x4137,map_normal_gain),C(0x4138,map_transient_gain),C(0x4e68,map_default),
    C(0x4e69,map_throttle_gain),C(0x4e6a,map_bias.limit),C(0x5d06,brake_delay)
};
#undef C
static const uint8_t io_bias_backing[8]={0x70,0x55,0x33,0x23,0x00,0x04,0x00,0x04 };
static const uint16_t io_outputs[]={0x47,0x4e,0x6a,0x6b,0x72,0x73,0x74,0x9c,0xfb,0x1c3,0x1c4,0x80c,0x80d,0x80e,0x303a,0x3062,0x3064,0x3067,0x3fc4,0x3fc5,0x3ffa,0x3ffb,0x3ffc,0x3ffd};
