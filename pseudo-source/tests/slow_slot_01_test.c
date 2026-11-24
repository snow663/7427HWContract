/* Slot01 source order: calibrated BARO, C668 speed, resident ADAA TCC. */
#define PCM_AIR_TEST_MAIN inherited_slot01_air_main
#include "fuel_air_test.c"
#undef PCM_AIR_TEST_MAIN
#include "scheduler.h"
static void setup(Fixture *f,Pcm *pcm,PcmCalibration *root,
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
    f->memory[0x5b6f]=0x12; f->memory[0x5b70]=0x34;
    f->memory[0x400f]=0; /* TCC skip case */
}
int main(int argc,char **argv)
{
    if(argc==2 && strcmp(argv[1],"--contracts")!=0)return 2;
    static Fixture f;Pcm pcm;PcmCalibration root;PcmFuelCalibration fuel;
    PcmIacCalibration iac;PcmAirCalibration air;PcmIoCalibration io;
#define SETUP() setup(&f,&pcm,&root,&fuel,&iac,&air,&io)
    SETUP();f.platform.enable_resident_slow_slots=false;
    /* PR48's complete C583/C668/ADAA chain is now default. This
     * fixture verifies the alternative chain below without demanding an
     * obsolete dependency task at the root. */
    CHECK(pcm_slot_01(&pcm)==PCM_OK);
    CHECK(f.memory[0xac]==0x12 && f.memory[0xad]==0x34);
    SETUP();
    CHECK(pcm_slot_01(&pcm)==PCM_OK);
    CHECK(f.memory[0xac]==0x12 && f.memory[0xad]==0x34);
    CHECK(pcm.spark.barometric_pressure!=0 && f.memory[0x854]==0);
    SETUP();f.memory[0x400f]=0x40;
    f.memory[0x1d9]=30;f.memory[0x284]=80;f.memory[0x6]=180;
    CHECK(pcm_slot_01(&pcm)==PCM_OK);
    CHECK(f.memory[0xac]==0x12 && f.memory[0xad]==0x34);
    CHECK(f.memory[0x854]==30);
    SETUP();f.platform.write16=NULL;
    CHECK(pcm_slot_01(&pcm)==PCM_NO_HARDWARE && f.memory[0x854]==0);
    SETUP();root.air=NULL;
    CHECK(pcm_slot_01(&pcm)==PCM_BAD_CONFIGURATION && f.memory[0xac]==0);
    CHECK(pcm_slot_01(NULL)==PCM_BAD_CONFIGURATION);
    puts("Slot01 real C583 -> C668 -> ADAA order, options and early-stop contracts pass.");
    return 0;
}
