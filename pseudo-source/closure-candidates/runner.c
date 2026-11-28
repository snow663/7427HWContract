#include "batch1.h"
#include "batch2.h"
#include "batch3.h"
#include <stdio.h>
#include <string.h>
static uint8_t image[65536], memory[65536];
static unsigned writes, fail_at;
static PcmStatus mask(void *ctx,bool on) { (void)ctx; printf(" %s",on?"sei":"cli"); return PCM_OK; }
static PcmStatus delay(void *ctx,uint16_t n) { (void)ctx; printf(" delay%u",(unsigned)n); return PCM_OK; }
static PcmStatus r8(void *ctx, uint16_t a, uint8_t *v)
{ (void)ctx; *v=memory[a]; return PCM_OK; }
static PcmStatus r16(void *ctx, uint16_t a, uint16_t *v)
{ (void)ctx; *v=(uint16_t)((uint16_t)memory[a]<<8)|memory[(uint16_t)(a+1u)]; return PCM_OK; }
static PcmStatus w8(void *ctx, uint16_t a, uint8_t v)
{ (void)ctx; printf(" b%04x%02x",(unsigned)a,(unsigned)v); if (++writes==fail_at) return PCM_NO_HARDWARE; memory[a]=v; return PCM_OK; }
static PcmStatus w16(void *ctx, uint16_t a, uint16_t v)
{ (void)ctx; printf(" w%04x%04x",(unsigned)a,(unsigned)v); if (++writes==fail_at) return PCM_NO_HARDWARE; memory[a]=(uint8_t)(v>>8); memory[(uint16_t)(a+1u)]=(uint8_t)v; return PCM_OK; }
int main(int argc,char **argv)
{
    if (argc!=2) return 2;
    FILE *file=fopen(argv[1],"rb");
    if (!file) return 2;
    if (fread(image,1,sizeof(image),file)!=sizeof(image)) { fclose(file); return 2; }
    fclose(file);
    PcmPlatform platform={.read8=r8,.read16=r16,.write8=w8,.write16=w16,.mask_irq=mask,.delay_cycles=delay};
    unsigned entry,passes,mutate,size;
    while (scanf("%x%u%u%u%u",&entry,&passes,&fail_at,&mutate,&size)==5) {
        if (mutate) return 2;
        memcpy(memory,image,sizeof(memory));
        for(unsigned i=0;i<size;++i) {
            unsigned a,v;
            if(scanf("%u%u",&a,&v)!=2 || a>=sizeof(memory) || v>255) return 2;
            memory[a]=(uint8_t)v;
        }
        Pcm pcm={.platform=&platform};
        writes=0;
        for(unsigned i=0;i<passes;++i) {
            uint16_t ratio=0;
            PcmStatus result;
            switch(entry) {
            case 0xb2b2: result=closure_gear_ratio(&pcm,&ratio); break;
            case 0xb2c9: result=closure_speed_ratio(&pcm); break;
            case 0xb2ed: result=closure_temperature_class(&pcm); break;
            case 0xe5cf: result=closure_fault_e5cf(&pcm); break;
            case 0xe5f1: result=closure_fault_e5f1(&pcm); break;
            case 0xe60b: result=closure_fault_e60b(&pcm); break;
            case 0xe6f5: result=closure_fault_e6f5(&pcm); break;
            case 0xe7c7: result=closure_diag_e7c7(&pcm); break;
            case 0xe808: result=closure_diag_e808(&pcm); break;
            case 0xe847: result=closure_diag_e847(&pcm); break;
            case 0xe8c8: result=closure_diag_e8c8(&pcm); break;
            case 0xeb81: result=closure_diag_eb81(&pcm); break;
            case 0xebc0: result=closure_diag_ebc0(&pcm); break;
            case 0xeccc: result=closure_diag_eccc(&pcm); break;
            case 0xef2b: result=closure_diag_ef2b(&pcm); break;
            case 0xaea4: result=closure_input_aea4(&pcm); break;
            case 0xb018: result=closure_input_b018(&pcm); break;
            case 0xb089: result=closure_input_b089(&pcm); break;
            case 0xb1f0: result=closure_input_b1f0(&pcm); break;
            case 0xb23c: result=closure_input_b23c(&pcm); break;
            case 0xc483: result=closure_input_c483(&pcm); break;
            case 0xe58c: result=closure_capture_e58c(&pcm,0xb9,(uint16_t)((uint16_t)memory[0x350]<<8|memory[0x351]),memory[0x352],&ratio); break;
            case 0xf420: result=closure_lag_f420(&pcm,(uint16_t)((uint16_t)memory[0x350]<<8|memory[0x351]),(uint16_t)((uint16_t)memory[0x352]<<8|memory[0x353]),0x5d0d,&ratio); break;
            case 0xf5a2: ratio=closure_mul_f5a2((uint16_t)((uint16_t)memory[0x350]<<8|memory[0x351]),(uint16_t)((uint16_t)memory[0x352]<<8|memory[0x353])); result=PCM_OK; break;
            default: return 2;
            }
            if(result!=PCM_OK && result!=PCM_NO_HARDWARE) return 1;
            if(entry==0xb2b2 && result==PCM_OK) printf(" x%04x",(unsigned)ratio);
            if((entry==0xe58c||entry==0xf420||entry==0xf5a2)&&result==PCM_OK) printf(" d%04x",(unsigned)ratio);
            printf(" %s ",result==PCM_OK?"ok":"failed");
            for(unsigned a=0;a<0x350;++a) printf("%02x",(unsigned)memory[a]);
            for(unsigned a=0x800;a<0x900;++a) printf("%02x",(unsigned)memory[a]);
            if(result!=PCM_OK) break;
        }
        putchar('\n');
    }
    return ferror(stdin)!=0;
}
