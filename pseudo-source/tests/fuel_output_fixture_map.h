#include "hardware.h"
#include "calibration.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { uint16_t address; uint8_t width, mask, count; size_t offset; } Mapping;
#define B(a,m) {a,8,0,1,offsetof(Pcm,m)}
#define W(a,m) {a,16,0,1,offsetof(Pcm,m)}
#define F(a,b,m) {a,0,b,1,offsetof(Pcm,m)}
static const Mapping reference_state_map[] = {
    F(0x44,0x01,runtime.factory_mode), F(0x44,0x10,reference.latch_inhibited),
    F(0x4f,0x10,runtime.fuel_running), F(0x50,0x20,reference.pending),
    F(0x50,0x01,reference.sample_map), F(0x04,0x10,scheduler.clear_after_run_count),
    F(0x19,0x40,reference.bank_fault), F(0x53,0x20,reference.crank_timer_latch),
    F(0x53,0x40,reference.split_latch), F(0x51,0x01,reference.packet_updated),
    F(0x51,0x80,reference.bank_latch), F(0x73,0x40,reference.extra_request),
    F(0x3f,0x10,reference.extra_guard), B(0x62,reference.rpm_coordinate),
    B(0x06,reference.coolant), B(0x55,reference.battery), B(0x67,reference.load_coordinate),
    B(0x1d9,reference.throttle), W(0x68,reference.load_filtered), W(0x6a,reference.load_event),
    B(0x2cd,reference.crank_references), B(0x2ce,reference.event_age),
    W(0x2cf,reference.crank_seed), W(0x24c,reference.delivered_pulse), W(0x250,reference.timer_pulse),
    B(0x256,reference.additive_offset), B(0x2c9,reference.enrichment), B(0x268,reference.enrichment_age),
    B(0x267,reference.enrichment_decrement), B(0x81e,reference.decay_count),
    B(0x84e,reference.bank_guard_count), W(0x254,reference.running_packet), W(0x81f,reference.timer_delay),
    W(0x821,reference.compare_a), W(0x823,reference.compare_b), W(0x825,reference.extended_a),
    W(0x827,reference.extended_b), B(0x829,reference.split_count), B(0x82a,reference.split_clear),
    B(0x82e,reference.map_sample), W(0x203,knock.sample_baseline),
    B(0x20d,knock.observation_accumulator)
};
#undef B
#undef W
#undef F
#define B(a,m) {a,8,0,1,offsetof(PcmCalibration,m)}
#define W(a,m) {a,16,0,1,offsetof(PcmCalibration,m)}
#define A(a,n,m) {a,8,0,n,offsetof(PcmCalibration,m)}
static const Mapping reference_cal_map[] = {
    A(0x465d,128,reference_compare_counts),
    A(0x45db,64,knock.noise_floor), A(0x461c,64,knock.observation_bias),
    B(0x400b,reference.mode_b), B(0x400c,reference.mode_c), B(0x400e,reference.mode_e),
    B(0x5b03,reference.diagnostic_options), A(0x4dcd,17,reference.crank_skip),
    A(0x4cbf,17,reference.decay_temperature), A(0x4cd0,17,reference.decay_event),
    A(0x4dde,24,reference.crank_cold), A(0x4df6,24,reference.crank_warm),
    A(0x4e0e,24,reference.crank_hot), A(0x4e26,8,reference.crank_repeat),
    A(0x4979,17,reference.short_pulse), B(0x4960,reference.crank_timer_gain),
    B(0x4964,reference.decay_interval), B(0x4d97,reference.crank_age_cap),
    B(0x4d98,reference.battery_limit), B(0x4d99,reference.coolant_gain_threshold),
    B(0x4e6f,reference.bank_guard_limit), B(0x4516,reference.load_minimum),
    B(0x48da,reference.throttle_limit), B(0x4518,reference.load_event_gain),
    W(0x4971,reference.short_subtract), W(0x492a,reference.running_packet_minimum)
};
#undef B
#undef W
#undef A
/* This explicit host adapter never prescribes native target struct layout. */
static uint16_t word(const uint8_t *memory, uint16_t address)
{ return (uint16_t)((uint16_t)memory[address] * 256u + memory[(uint16_t)(address + 1u)]); }
static void transfer(void *object, uint8_t *memory, const Mapping *mapping, size_t count, bool load)
{
    for (size_t i=0;i<count;++i) {
        const Mapping *m=&mapping[i]; uint8_t *field=(uint8_t *)object+m->offset;
        if (m->address==0x465d) { /* Explicit big-endian table words, not memcpy. */
            for (unsigned j=0;j<64;++j) {
                volatile uint16_t *item=(volatile uint16_t *)(void *)(field+2*j);
                if (load) *item=word(memory,(uint16_t)(m->address+2*j));
                else { memory[m->address+2*j]=(uint8_t)(*item>>8);memory[m->address+2*j+1]=(uint8_t)*item; }
            }
        } else if (m->mask) {
            volatile bool *item=(volatile bool *)(void *)field;
            if (load) *item=(memory[m->address]&m->mask)!=0;
            else memory[m->address]=(uint8_t)((memory[m->address]&(uint8_t)~m->mask)|(*item?m->mask:0));
        } else if (m->width==16) {
            volatile uint16_t *item=(volatile uint16_t *)(void *)field;
            if (load) *item=word(memory,m->address);
            else { memory[m->address]=(uint8_t)(*item>>8);memory[m->address+1]=(uint8_t)*item; }
        } else for (unsigned j=0;j<m->count;++j) {
            volatile uint8_t *item=field+j;
            if (load) *item=memory[m->address+j];else memory[m->address+j]=*item;
        }
    }
}

#define B(a,m) {a,8,0,1,offsetof(Pcm,m)}
#define W(a,m) {a,16,0,1,offsetof(Pcm,m)}
#define F(a,b,m) {a,0,b,1,offsetof(Pcm,m)}
static const Mapping fuel_state_map[] = {
 B(2,scheduler.phase), F(0x1a,2,runtime.adc_timeout), F(0x3a,1,runtime.adc_fault),
 B(0x3e,io.coolant_context), F(0x3f,0x80,fuel.short_pulse),
 B(0xa6,fuel.raw_throttle), B(0xa7,spark.battery_sample), B(0x1d5,fuel.raw_oxygen),
 B(0x14e,fuel.measured_current), W(0x205,spark.bypass_baseline),
 W(0x24e,fuel.corrected_pulse), W(0x5f,spark.period_basis),
 B(7,iac.position),B(8,iac.target),B(9,iac.state_flags),B(10,iac.step_control),
 B(0x4c,transmission.output_shadow),
 B(0x82d,io.raw_coolant),B(0x1a1,io.auxiliary_sample),B(0xa5,io.auxiliary_reference),
 B(0x82f,io.diagnostic_sample)
};
#undef B
#undef W
#undef F
#define B(a,m) {a,8,0,1,offsetof(PcmFuelCalibration,m)}
#define W(a,m) {a,16,0,1,offsetof(PcmFuelCalibration,m)}
#define A(a,n,m) {a,8,0,n,offsetof(PcmFuelCalibration,m)}
static const Mapping fuel_cal_map[] = {
 W(0x496d,synchronous_minimum),W(0x496f,synchronous_replacement),
 B(0x4973,injection_delay_gain),A(0x4b05,17,offset)
};
#undef B
#undef W
#undef A
#define SIZE(a) (sizeof(a)/sizeof((a)[0]))
