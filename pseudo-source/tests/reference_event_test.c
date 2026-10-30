#include "hardware.h"
#include "calibration.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { uint16_t address; uint8_t width, mask, count; size_t offset; } Mapping;
#define B(a,m) {a,8,0,1,offsetof(Pcm,m)}
#define W(a,m) {a,16,0,1,offsetof(Pcm,m)}
#define F(a,b,m) {a,0,b,1,offsetof(Pcm,m)}
static const Mapping state_map[] = {
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
    B(0x82e,reference.map_sample)
};
#undef B
#undef W
#undef F
#define B(a,m) {a,8,0,1,offsetof(PcmCalibration,m)}
#define W(a,m) {a,16,0,1,offsetof(PcmCalibration,m)}
#define A(a,n,m) {a,8,0,n,offsetof(PcmCalibration,m)}
static const Mapping cal_map[] = {
    A(0x465d,128,reference_compare_counts),
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
typedef struct { char kind; unsigned width; uint16_t address,value; } Event;
typedef struct {
    uint8_t memory[65536]; Event events[128];
    unsigned used,attempts,fail_at,timer_reads;uint16_t timer_seed,timer_step;
    PcmPlatform platform;
} Fixture;
static PcmStatus record(Fixture *f,char kind,unsigned width,uint16_t address,uint16_t value)
{
    if (++f->attempts==f->fail_at) return PCM_NO_HARDWARE;
    if (f->used>=128) exit(3);
    f->events[f->used++]=(Event){kind,width,address,value};return PCM_OK;
}
static PcmStatus read8(void *v,uint16_t a,uint8_t *out)
{
    Fixture *f=v;uint8_t value=f->memory[a];PcmStatus r=record(f,'R',8,a,value);
    if (r==PCM_OK) *out=value;
    return r;
}
static PcmStatus read16(void *v,uint16_t a,uint16_t *out)
{
    Fixture *f=v;uint16_t value=a==PCM_TCNT?(uint16_t)(f->timer_seed+f->timer_reads*f->timer_step):word(f->memory,a);
    PcmStatus r=record(f,'R',16,a,value);if (r==PCM_OK) { *out=value;if (a==PCM_TCNT) ++f->timer_reads; }return r;
}
static PcmStatus write8(void *v,uint16_t a,uint8_t value)
{
    Fixture *f=v;PcmStatus r=record(f,'W',8,a,value);
    if (r==PCM_OK) { if (a==PCM_TFLG1) f->memory[a]&=(uint8_t)~value;else f->memory[a]=value; }return r;
}
static PcmStatus write16(void *v,uint16_t a,uint16_t value)
{
    Fixture *f=v;PcmStatus r=record(f,'W',16,a,value);
    if (r==PCM_OK) { f->memory[a]=(uint8_t)(value>>8);f->memory[a+1]=(uint8_t)value; }return r;
}
static PcmStatus delay(void *v,uint16_t cycles) { return record(v,'D',0,0,cycles); }
static void hex(const uint8_t *memory,unsigned start,unsigned end)
{ for (unsigned a=start;a<end;++a) printf("%02x",memory[a]); }
static const unsigned blocks[][2]={{0,0x900},{0x3000,0x3070},{0x3fc0,0x3ffe},{0x4000,0x5b04}};
int main(int argc,char **argv)
{
    static Fixture f;
    if (argc==2&&strcmp(argv[1],"--defaults")==0) {
        PcmCalibration cal=pcm_reference_scheduler_calibration;
        transfer(&cal,f.memory,cal_map,sizeof(cal_map)/sizeof(cal_map[0]),false);
        printf("[");bool first=true;
        for (size_t i=0;i<sizeof(cal_map)/sizeof(cal_map[0]);++i) {
            const Mapping *m=&cal_map[i];unsigned size=m->width==16?2:m->count;
            for (unsigned j=0;j<size;++j) { printf("%s[%u,%u]",first?"":",",m->address+j,f.memory[m->address+j]);first=false; }
        }
        puts("]");return 0;
    }
    bool helper=argc==2&&strcmp(argv[1],"--crank-timer")==0;
    unsigned step,fail;
    while (scanf("%u %u",&step,&fail)==2) {
        if (step>65535) return 2;
        memset(&f,0,sizeof(f));f.timer_step=(uint16_t)step;f.fail_at=fail;
        for (size_t b=0;b<4;++b) for (unsigned a=blocks[b][0];a<blocks[b][1];++a) {
            unsigned value;if (scanf("%2x",&value)!=1) return 2;f.memory[a]=(uint8_t)value;
        }
        f.timer_seed=word(f.memory,PCM_TCNT);
        f.platform.context=&f;f.platform.read8=read8;f.platform.read16=read16;
        f.platform.write8=write8;f.platform.write16=write16;f.platform.delay_cycles=delay;
        Pcm pcm={0};PcmCalibration cal=pcm_reference_scheduler_calibration;
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),true);
        transfer(&cal,f.memory,cal_map,sizeof(cal_map)/sizeof(cal_map[0]),true);
        pcm.platform=&f.platform;pcm.calibration=&cal;pcm.unresolved_task=PCM_TASK_COUNT;
        PcmStatus status=helper?pcm_reference_crank_timer(&pcm):pcm_reference_irq(&pcm);
        transfer(&pcm,f.memory,state_map,sizeof(state_map)/sizeof(state_map[0]),false);
        printf("{\"status\":%u,\"ram\":\"",(unsigned)status);hex(f.memory,0,0x900);
        printf("\",\"io\":\"");hex(f.memory,0x3000,0x3070);hex(f.memory,0x3fc0,0x3ffe);
        printf("\",\"events\":[");
        for (unsigned i=0;i<f.used;++i) { const Event *e=&f.events[i];printf("%s[\"%c\",%u,%u,%u]",i?",":"",e->kind,e->width,e->address,e->value); }
        puts("]}");
    }
    return 0;
}
