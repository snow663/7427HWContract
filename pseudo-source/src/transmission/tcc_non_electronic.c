#include "board_io.h"
#include "hardware.h"
/* Stock BMHM $ADAA..$AE5B, non-electronic TCC request qualification.
 * This controls logical RAM $0089.5; it does not drive a physical TCC
 * coil here. F4C1 is the unsigned 16-spaced table interpolation using
 * MUL rounding; F4BD first subtracts the $40 input offset. */
#define TCC_RUN(call) do { PcmStatus x=(call);if(x!=PCM_OK)return x; }while(0)
static PcmStatus table16(Pcm *p,uint16_t start,uint8_t sample,uint8_t *out)
{
    uint16_t product=(uint16_t)sample*16u;
    uint16_t cell=(uint16_t)(start+(product>>8));
    uint16_t packed;
    TCC_RUN(pcm_read16(p,cell,&packed));
    uint8_t first=(uint8_t)(packed>>8),last=(uint8_t)packed;
    uint8_t diff=first<last?(uint8_t)(last-first):(uint8_t)(first-last);
    uint8_t step=(uint8_t)(((uint16_t)diff*(uint8_t)product+128u)>>8);
    uint8_t fresh;
    TCC_RUN(pcm_read8(p,cell,&fresh));
    *out=last>first?(uint8_t)(fresh+step):(uint8_t)(fresh-step);
    return PCM_OK;
}
static PcmStatus flag8(Pcm *p,uint16_t address,uint8_t bit,bool enabled)
{
    return pcm_update8(p,address,enabled?0u:bit,enabled?bit:0u);
}
PcmStatus pcm_tcc_non_electronic(Pcm *pcm)
{
    if(pcm==NULL)return PCM_BAD_CONFIGURATION;
    uint8_t mode,speed,throttle,lock,limit,from_table,delta,old,delay,requested;
    TCC_RUN(pcm_read8(pcm,0x400fu,&mode)); /* ADAA */
    if(!(mode&0x40u))return PCM_OK;
    TCC_RUN(pcm_read8(pcm,0x0284u,&speed));
    /* MUL A*205 -> ASLA; A is rounded/truncated high byte doubled. */
    uint8_t scaled=(uint8_t)((((uint16_t)speed*205u)>>8)*2u);
    TCC_RUN(table16(pcm,0x5168u,scaled,&from_table));
    TCC_RUN(pcm_read8(pcm,0x0089u,&lock));
    uint16_t boundary=(lock&0x20u)?0x5161u:0x5160u;
    if(lock&0x20u) {
        TCC_RUN(pcm_read8(pcm,0x515bu,&limit));
        from_table=from_table>=limit?(uint8_t)(from_table-limit):0u;
    }
    TCC_RUN(pcm_read8(pcm,0x01d9u,&throttle));
    if(throttle<from_table) {
        TCC_RUN(pcm_read8(pcm,0x515fu,&delay));
        TCC_RUN(pcm_write8(pcm,0x0853u,delay));
        goto release;
    }
    TCC_RUN(pcm_read8(pcm,0x0284u,&speed));
    TCC_RUN(pcm_read8(pcm,boundary,&limit));
    if(speed>=limit)goto request_lock;
    TCC_RUN(pcm_read8(pcm,0x0006u,&requested));
    TCC_RUN(pcm_read8(pcm,0x515au,&limit));
    if(requested<limit)goto unqualified;
    TCC_RUN(pcm_read8(pcm,0x01d9u,&throttle));
    TCC_RUN(pcm_read8(pcm,0x0854u,&old));
    delta=throttle>=old?(uint8_t)(throttle-old):(uint8_t)(old-throttle);
    TCC_RUN(pcm_read8(pcm,throttle<old?0x515cu:0x515du,&limit));
    if(delta>limit)goto unqualified;
    TCC_RUN(pcm_read8(pcm,0x004du,&requested));
    boundary=(uint16_t)(0x5164u+((requested&1u)?2u:0u)+((lock&0x20u)?1u:0u));
    TCC_RUN(pcm_read8(pcm,0x0284u,&speed));
    TCC_RUN(pcm_read8(pcm,boundary,&limit));
    if(speed<=limit)goto unqualified;
    boundary=(lock&0x20u)?0x5171u:0x517eu;
    uint16_t rpm_limit=(lock&0x20u)?0x5162u:0x5163u;
    /* $AE29 MUL speed*205 -> ASLA twice; subtract B=$40 and clamp. */
    scaled=(uint8_t)((((uint16_t)speed*205u)>>8)*4u);
    scaled=scaled>=64u?(uint8_t)(scaled-64u):0u;
    TCC_RUN(table16(pcm,boundary,scaled,&from_table));
    TCC_RUN(pcm_read8(pcm,0x01d9u,&throttle));
    if(from_table<throttle)goto unqualified;
    TCC_RUN(pcm_read8(pcm,0x0063u,&requested));
    TCC_RUN(pcm_read8(pcm,rpm_limit,&limit));
    if(requested<limit)goto unqualified;
    TCC_RUN(pcm_read8(pcm,0x0853u,&delay));
    if(delay!=0u) {
        delay--;
        TCC_RUN(pcm_write8(pcm,0x0853u,delay));
        goto release;
    }
request_lock:
    TCC_RUN(flag8(pcm,0x0089u,0x20u,true));
    goto save_tps;
unqualified:
    TCC_RUN(pcm_read8(pcm,0x515eu,&delay));
    TCC_RUN(pcm_write8(pcm,0x0853u,delay));
release:
    TCC_RUN(flag8(pcm,0x0089u,0x20u,false));
save_tps:
    TCC_RUN(pcm_read8(pcm,0x01d9u,&throttle));
    return pcm_write8(pcm,0x0854u,throttle);
}
