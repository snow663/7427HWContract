#define B(a,m) {a,8,0,1,offsetof(Pcm,m)}
#define W(a,m) {a,16,0,1,offsetof(Pcm,m)}
#define F(a,b,m) {a,0,b,1,offsetof(Pcm,m)}
#define A(a,n,m) {a,8,0,n,offsetof(Pcm,m)}
static const Mapping serial_state_map[] = {
 B(0x42,serial.sessions),B(0x45,serial.clear_edges),
 F(0x3b,1,serial.clear_transmission),F(0x3b,2,serial.clear_engine),
 F(0x3b,4,runtime.monitor_freeze),F(0x3b,8,runtime.transmission_service),
 F(0x3b,0x20,serial.deferred),F(0x3b,0x40,serial.busy),F(0x3b,0x80,serial.companion_pending),
 B(0x360,serial.count),B(0x361,serial.checksum),W(0x362,serial.descriptor),
 B(0x364,serial.last_id),B(0x365,serial.length),B(0x366,serial.companion),B(0x367,serial.receive_age),
 W(0x368,serial.service_age),W(0x36a,serial.service_expiry),A(0x36c,34,serial.receive),
 B(0x38e,serial.engine_command),B(0x399,serial.transmission_command),B(0x49,system.startup_counter),
 F(0x50,8,io.diagnostic_warm),F(0x38f,1,transmission.shift_service_enable),F(0x390,1,transmission.shift_service_value),
 F(0x38f,4,runtime.service_output_enable),F(0x390,4,runtime.service_output_value),
 F(0x391,0x80,runtime.inhibit_heartbeat),F(0x391,8,spark.service_bypass),
 F(0x391,0x20,iac.service_reset),F(0x38f,0x40,iac.service_kicker),F(0x390,0x40,iac.service_kicker_value),
 B(0x396,iac.service_value),B(0x39a,transmission.current_service_enable),B(0x39b,transmission.current_service_value),
 B(3,scheduler.busy_phase),W(0x1ee,spark.command),W(0x1f0,spark.command_latched),W(0x88b,iac.airflow),
};
#undef B
#undef W
#undef F
#undef A
