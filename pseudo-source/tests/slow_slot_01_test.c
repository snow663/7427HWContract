/* Slot01 transitive source-order fixture with stock-calibrated BARO input. */
#define PCM_AIR_TEST_MAIN inherited_slot01_air_main
#include "fuel_air_test.c"
#undef PCM_AIR_TEST_MAIN
#include "scheduler.h"
static unsigned call_count;static uint16_t call_pc;
static PcmStatus address_call(void *ctx,uint16_t address)
{
    (void)ctx;call_pc=address;++call_count;return PCM_OK;
}
static void slot1_setup(Fixture *f,Pcm *pcm,PcmCalibration *root,
                        PcmFuelCalibration *fuel,PcmIacCalibration *iac,
                        PcmAirCalibration *air,PcmIoCalibration *io)
{
    air_init(f,pcm,root,fuel,iac,air,io);
    f->platform.task[PCM_SLOT_01]=NULL;
    f->platform.enable_resident_slow_slots=true;
    air->baro_options=0;
    pcm->reference.latch_inhibited=true;
    pcm->spark.map_filtered=100;
    pcm->spark.barometric_high=99;
    pcm->reference.coolant=180;
    pcm->reference.throttle=30;
    pcm->spark.rpm_low_coordinate=60;
    f->memory[0x5b30]=4;
    f->memory[0x1b]=4;
    f->memory[0x5b6f]=0x12;
    f->memory[0x5b70]=0x34;
    call_count=0;call_pc=0;
}
int main(int argc,char **argv)
{
    if(argc==2 && strcmp(argv[1],"--contracts")!=0)return 2;
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;
    PcmIacCalibration iac;PcmAirCalibration air;PcmIoCalibration io;
#define SETUP() slot1_setup(&f,&pcm,&root,&fuel,&iac,&air,&io)
    SETUP();f.platform.enable_resident_slow_slots=false;
    CHECK(pcm_slot_01(&pcm)==PCM_UNIMPLEMENTED && pcm.unresolved_task==PCM_SLOT_01);
    CHECK(f.memory[0xac]==0 && f.memory[0xad]==0 && call_count==0);
    SETUP();
    CHECK(pcm_slot_01(&pcm)==PCM_UNIMPLEMENTED && pcm.unresolved_task==PCM_SLOT_01);
    CHECK(f.memory[0xac]==0x12 && f.memory[0xad]==0x34);
    CHECK(pcm.spark.barometric_pressure!=0 && call_count==0);
    SETUP();f.platform.call_address=address_call;
    CHECK(pcm_slot_01(&pcm)==PCM_OK && call_count==1 && call_pc==0xadaau);
    CHECK(f.memory[0xac]==0x12 && f.memory[0xad]==0x34);
    SETUP();f.platform.call_address=address_call;
    f.platform.write16=NULL;
    CHECK(pcm_slot_01(&pcm)==PCM_NO_HARDWARE && call_count==0);
    SETUP();f.platform.call_address=address_call;root.air=NULL;
    CHECK(pcm_slot_01(&pcm)==PCM_BAD_CONFIGURATION && call_count==0);
    CHECK(pcm_slot_01(NULL)==PCM_BAD_CONFIGURATION);
    puts("Slot01 C583 -> C668 -> explicit ADAA boundary, gated order and partial failures pass.");
    return 0;
}
