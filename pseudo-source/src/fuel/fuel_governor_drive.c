#include "fuel.h"
#include "hardware.h"
#define GOV_RUN(call) do { PcmStatus s=(call);if(s!=PCM_OK)return s; } while(0)

/* BMHM F4B6/F4C5: the table's first byte supplies the segment scale.
 * LDD samples adjacent knots together; ADCA 0,X samples the first knot
 * again after MUL, so the last read must be separate for mutable providers. */
static PcmStatus governor_curve(Pcm *pcm,uint16_t table,uint8_t input,uint8_t *out)
{
    uint8_t scale,base;
    uint16_t knots;
    GOV_RUN(pcm_read8(pcm,table,&scale));
    uint16_t point=(uint16_t)((uint16_t)input*scale);
    uint16_t index=(uint16_t)(point>>8);
    uint16_t start=(uint16_t)(table+1u+index);
    GOV_RUN(pcm_read16(pcm,start,&knots));
    uint8_t first=(uint8_t)(knots>>8),second=(uint8_t)knots;
    uint8_t diff=first>=second?(uint8_t)(first-second):(uint8_t)(second-first);
    uint8_t step=(uint8_t)(((uint16_t)diff*(uint8_t)point+128u)>>8);
    GOV_RUN(pcm_read8(pcm,start,&base));
    *out=first<second?(uint8_t)(base+step):(uint8_t)(base-step);
    return PCM_OK;
}

/* BMHM 90D3..9166, optional actuator duty controller, JSR at 7E3D.
 * A missing target driver returns NO_HARDWARE instead of assuming a safe
 * physical output. The caller qualifies the $400F.0 option. */
PcmStatus pcm_fuel_governor_drive(Pcm *pcm)
{
    if(pcm==NULL)return PCM_BAD_CONFIGURATION;
    uint8_t desired=pcm->transmission.governor_requested_throttle;
    uint8_t actual=pcm->reference.throttle;
    uint8_t error=desired>=actual?(uint8_t)(desired-actual):(uint8_t)(actual-desired);
    pcm->transmission.governor_throttle_error=error; /* 029A */
    uint8_t proportional,integral_gain;
    GOV_RUN(governor_curve(pcm,0x50ffu,error,&proportional));
    uint32_t product=(uint32_t)proportional*error*4u;
    uint16_t proportional_term=(uint16_t)(product>65535u?65535u:product);
    pcm->transmission.governor_proportional=proportional_term; /* 0295 */
    GOV_RUN(governor_curve(pcm,0x5109u,error,&integral_gain));
    uint16_t integral_term=(uint16_t)((uint16_t)integral_gain*error);
    pcm->transmission.governor_integral_gain=integral_term; /* 0297 */

    uint16_t accumulator=pcm->transmission.governor_integrator; /* 0288 */
    uint8_t pwm;
    if(desired<actual) { /* 9112: increasing actuator demand */
        uint32_t advanced=(uint32_t)accumulator+integral_term;
        accumulator=(uint16_t)(advanced>65535u?0xff00u:advanced);
        pcm->transmission.governor_integrator=accumulator;
        uint32_t output=(uint32_t)accumulator+proportional_term+128u;
        pwm=(uint8_t)(output>65535u?255u:(output>>8));
    } else { /* 912B: subtract I/P, floor at zero */
        accumulator=accumulator>=integral_term?(uint16_t)(accumulator-integral_term):0u;
        pcm->transmission.governor_integrator=accumulator;
        if(accumulator<proportional_term)pwm=0;
        else {
            uint32_t output=(uint32_t)(accumulator-proportional_term)+128u;
            pwm=(uint8_t)(output>65535u?255u:(output>>8));
        }
    }
    if(desired==255u) pcm->transmission.governor_integrator=0; /* 9141..9148 */

    uint8_t flags;
    GOV_RUN(pcm_read8(pcm,0x0051u,&flags));
    if(flags&0x10u) pwm=0;
    else {
        GOV_RUN(pcm_read8(pcm,0x003bu,&flags));
        if(flags&0x10u) {
            GOV_RUN(pcm_read8(pcm,0x0393u,&flags));
            if(flags&1u) GOV_RUN(pcm_read8(pcm,0x0394u,&pwm));
        }
    }
    return pcm_write16(pcm,0x306cu,(uint16_t)(0x1f00u|pwm));
}
