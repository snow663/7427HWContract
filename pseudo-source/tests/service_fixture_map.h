#define B(a,m) {a,8,0,1,offsetof(Pcm,m)}
#define F(a,b,m) {a,0,b,1,offsetof(Pcm,m)}
#define A(a,n,m) {a,8,0,n,offsetof(Pcm,m)}
static const Mapping service_state_map[]={
 F(0x44,4,runtime.output_override),F(0x44,0x80,spark.bypass_fault_latched),F(4,0x80,spark.bypass_supervision),F(0x19,0x20,spark.est_fault),F(0x19,0x10,knock.sensor_fault),B(0x8e,transmission.output_fault_flags),B(0x89,transmission.range_context),B(0x1c,transmission.fault_flags_primary),B(0x1d,transmission.fault_flags_secondary),
 B(0x398,spark.service_amount),B(0x15,system.diagnostic_checksum),B(0x103,transmission.service_gear),
 B(0x10a,transmission.service_tcc),B(0x111,transmission.service_pressure),
 B(0x118,transmission.service_state),B(0x11a,transmission.adaptive_flags),
 A(0x130,2,transmission.diagnostic_status),
};
#undef B
#undef A
#undef F
