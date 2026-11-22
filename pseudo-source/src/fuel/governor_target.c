#include "governor_internal.h"
/*8EB4..90D2. Retain accumulator0286, actuator integral0288, lead0290 and
 * published target0299 as distinct values. Live flag/limit reads stay ordered. */
PcmStatus pcm_governor_target(Pcm *pcm)
{
    uint8_t flags,value,reference,error,gain,command=255,derivative;
    uint16_t integral,step,lead,word;bool clamped;
    SYS_RUN(pcm_read8(pcm,0x400f,&flags));if (!(flags&1u)) goto disabled;
    SYS_RUN(pcm_read8(pcm,0x004f,&flags));if (!(flags&0x80u)) goto disabled;
    SYS_RUN(pcm_read8(pcm,0x006f,&flags));if (flags&0x34u) goto disabled;
    SYS_RUN(sys_update(pcm,0x0075,4,0));SYS_RUN(pcm_read8(pcm,0x50d8,&reference));
    SYS_RUN(pcm_read8(pcm,0x028e,&value));
    error=reference>=value?(uint8_t)(reference-value):(uint8_t)(value-reference);
    if (reference<value) SYS_RUN(sys_update(pcm,0x0075,0,4));
    SYS_RUN(pcm_write8(pcm,0x0293,error));SYS_RUN(pcm_read8(pcm,0x0086,&flags));
    if (flags&0x40u) {
        pcm->governor.extension_value=error;pcm->governor.extension_carry=false;
        SYS_RUN(pcm_run_task(pcm,PCM_GOVERNOR_EXTENSION));
        if (pcm->governor.extension_carry) return pcm_write8(pcm,0x0299,pcm->governor.extension_value);
    }
    SYS_RUN(pcm_read8(pcm,0x50da,&reference));
    if (reference!=0) {
        SYS_RUN(pcm_read16(pcm,0x0284,&word));SYS_RUN(pcm_read8(pcm,0x50da,&reference));
        bool below=(word>>8)<reference;word=(uint16_t)(word-(uint16_t)reference*256u);
        if (below) word=(uint16_t)(0u-word);
        word=word>16383u?65535:(uint16_t)(word*4u);value=(uint8_t)(word>>8);
        SYS_RUN(pcm_write8(pcm,0x0294,value));
        if (!below) {
            SYS_RUN(sys_update(pcm,0x0075,0,0x40));SYS_RUN(pcm_read8(pcm,0x0075,&flags));
            if (!(flags&0x80u)) {
                SYS_RUN(pcm_read8(pcm,0x50e1,&value));SYS_RUN(pcm_read8(pcm,0x01d9,&reference));
                if (value>=reference) SYS_RUN(pcm_read8(pcm,0x01d9,&value));
                SYS_RUN(pcm_write8(pcm,0x0286,value));SYS_RUN(sys_update(pcm,0x0075,0,0x80));
            }
            goto speed_active;
        }
        SYS_RUN(sys_update(pcm,0x0075,0x40,0));SYS_RUN(pcm_read8(pcm,0x0075,&flags));
        if (flags&0x80u) {
            SYS_RUN(pcm_read8(pcm,0x50db,&reference));if (value<reference) goto speed_active;
        }
    }
    SYS_RUN(sys_update(pcm,0x0075,0x80,0));goto rpm;
speed_active:
    SYS_RUN(sys_update(pcm,0x0075,0x13,0));
rpm:
    SYS_RUN(pcm_read8(pcm,0x0075,&flags));
    if (flags&4u) {
        SYS_RUN(pcm_read8(pcm,0x0075,&flags));
        if (!(flags&0x81u)) {
            SYS_RUN(pcm_read8(pcm,0x01d9,&value));SYS_RUN(pcm_read8(pcm,0x0286,&reference));
            if (value<=reference) SYS_RUN(pcm_write8(pcm,0x0286,value));
        }
        SYS_RUN(sys_update(pcm,0x0075,0,1));SYS_RUN(sys_update(pcm,0x0075,0x12,0));
    }
    SYS_RUN(pcm_read8(pcm,0x0075,&flags));if (!(flags&0x81u)) goto anticipate;
    SYS_RUN(pcm_read8(pcm,0x0299,&value));SYS_RUN(gov_capped(pcm,(uint8_t)(value>>1),0x50e8,&gain));
    SYS_RUN(pcm_read8(pcm,0x0294,&error));SYS_RUN(pcm_read8(pcm,0x0075,&flags));
    uint16_t coefficient=(flags&1u)?0x50e0:0x50df;
    if (flags&1u) SYS_RUN(pcm_read8(pcm,0x0293,&error));
    SYS_RUN(pcm_write16(pcm,0x028a,gov_product(gain,error,3)));
    SYS_RUN(pcm_read8(pcm,coefficient,&gain));SYS_RUN(gov_gain_word(pcm,0x028a,gain,&step));
    SYS_RUN(pcm_write16(pcm,0x028a,step));SYS_RUN(pcm_read8(pcm,0x50dd,&gain));
    SYS_RUN(pcm_read8(pcm,0x0293,&error));lead=gov_product(gain,error,2);
    SYS_RUN(pcm_write16(pcm,0x0290,lead));SYS_RUN(pcm_write8(pcm,0x0292,0));
    SYS_RUN(pcm_read8(pcm,0x0075,&flags));
    if (flags&0x80u) {
        SYS_RUN(pcm_read8(pcm,0x0294,&error));SYS_RUN(pcm_read8(pcm,0x50de,&gain));
        lead=gov_product(error,gain,4);SYS_RUN(pcm_write8(pcm,0x0292,(uint8_t)(lead>>8)));
        SYS_RUN(pcm_read8(pcm,0x0075,&flags));
        if (!(flags&4u)) SYS_RUN(pcm_write16(pcm,0x0290,lead));
    }
    SYS_RUN(pcm_read8(pcm,0x0075,&flags));SYS_RUN(pcm_read16(pcm,0x0286,&integral));
    SYS_RUN(pcm_read16(pcm,0x028a,&step));
    if (flags&0x44u) {
        bool borrowed=integral<step;integral=(uint16_t)(integral-step);
        SYS_RUN(gov_floor(pcm,(uint8_t)(integral>>8),borrowed,0x50e2,&command,&clamped));
        if (clamped) { integral=(uint16_t)((uint16_t)command*256u);goto store; }
        SYS_RUN(pcm_write16(pcm,0x0286,integral));SYS_RUN(pcm_read16(pcm,0x0290,&lead));
        borrowed=integral<lead;word=(uint16_t)(integral-lead);
        SYS_RUN(gov_floor(pcm,(uint8_t)(word>>8),borrowed,0x50e2,&command,&clamped));
    } else {
        uint32_t sum=(uint32_t)integral+step;integral=sum>65535u?65535:(uint16_t)sum;
        SYS_RUN(pcm_write16(pcm,0x0286,integral));SYS_RUN(pcm_read16(pcm,0x0290,&lead));
        sum=(uint32_t)integral+lead;command=sum>65535u?255:(uint8_t)(sum>>8);
    }
    goto publish;
anticipate:
    SYS_RUN(pcm_write8(pcm,0x0292,0));SYS_RUN(pcm_read8(pcm,0x0075,&flags));
    if (!(flags&2u)) {
        SYS_RUN(pcm_read8(pcm,0x028d,&value));if (value&0x80u) goto maximum;
        if (value>32u) value=32;
        SYS_RUN(gov_scaled(pcm,value,0x50ee,&value));SYS_RUN(pcm_read8(pcm,0x028e,&reference));
        if (value>=reference) goto maximum;
        SYS_RUN(sys_update(pcm,0x0075,0,2));SYS_RUN(pcm_read8(pcm,0x50e1,&command));
        SYS_RUN(pcm_read8(pcm,0x01d9,&reference));
        if (command>reference) SYS_RUN(pcm_read8(pcm,0x01d9,&command));
        SYS_RUN(gov_floor(pcm,command,false,0x50e3,&command,&clamped));
        integral=(uint16_t)((uint16_t)command*256u);goto store;
    }
    SYS_RUN(pcm_read8(pcm,0x0075,&flags));
    if (!(flags&0x10u)) {
        SYS_RUN(pcm_read8(pcm,0x028d,&derivative));
        if (derivative>0 && derivative<128u) goto reduce;
    }
    SYS_RUN(sys_update(pcm,0x0075,0,0x10));SYS_RUN(pcm_read8(pcm,0x0299,&value));
    SYS_RUN(pcm_read8(pcm,0x50e6,&gain));SYS_RUN(pcm_read8(pcm,0x50e5,&reference));
    if (value<reference) SYS_RUN(pcm_read8(pcm,0x50e7,&gain));
    SYS_RUN(pcm_read8(pcm,0x0293,&error));SYS_RUN(pcm_read16(pcm,0x0286,&integral));
    uint32_t sum=(uint32_t)integral+(uint16_t)error*gain;if (sum>65535u) goto maximum;
    integral=(uint16_t)sum;command=(uint8_t)(integral>>8);goto store;
reduce:
    SYS_RUN(pcm_read8(pcm,0x0006,&value));if (value>128u) value=128;
    SYS_RUN(sys_curve16(pcm,(uint8_t)(value>>1),0x50fa,&gain));
    SYS_RUN(pcm_read8(pcm,0x028d,&derivative));word=gov_product(gain,derivative,2);
    SYS_RUN(pcm_read8(pcm,0x0286,&value));error=(uint8_t)(word>>8);command=(uint8_t)(value-error);
    SYS_RUN(pcm_read8(pcm,0x0287,&reference));
    SYS_RUN(gov_floor(pcm,command,value<error,0x50e3,&command,&clamped));
    /*9086 still samples the old fraction, but both successors join9093 CLRB. */
    integral=(uint16_t)((uint16_t)command*256u);goto store;
maximum:
    command=255;integral=0xff00;
store:
    SYS_RUN(pcm_write16(pcm,0x0286,integral));
publish:
    SYS_RUN(pcm_read8(pcm,0x0075,&flags));
    if (flags&0x84u) {
        uint8_t direction;SYS_RUN(pcm_read8(pcm,0x0075,&direction));
        SYS_RUN(pcm_read8(pcm,0x0292,&value));
        if (direction&0x40u) SYS_RUN(gov_floor(pcm,(uint8_t)(command-value),command<value,0x50e2,&command,&clamped));
        else { unsigned total=(unsigned)command+value;command=total>255u?255:(uint8_t)total; }
    }
    SYS_RUN(pcm_write8(pcm,0x0299,command));
    if (!(flags&0x11u)) return PCM_OK;
    SYS_RUN(pcm_read8(pcm,0x0288,&value));if (value!=0) return PCM_OK;
    SYS_RUN(pcm_read8(pcm,0x0075,&flags));
    if (flags&1u) {
        SYS_RUN(pcm_read8(pcm,0x028e,&value));SYS_RUN(pcm_read8(pcm,0x50d9,&reference));
        if (value>=reference) return PCM_OK;
    }
    return sys_update(pcm,0x0075,0x13,0);
disabled:
    return pcm_write8(pcm,0x0299,255);
}
