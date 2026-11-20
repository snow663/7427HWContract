#include "fuel.h"
#include "hardware.h"
#define F_RUN(call) do { PcmStatus s=(call);if(s!=PCM_OK)return s; } while(0)

/* BMHM $7D4B..$7DB5. The following $7DB6 MAP/TPS/O2 prefix and the
 * $852C scheduled tail are separate: this routine never admits delivery.
 * Every read/write is through the logical address provider, not struct RAM. */
static PcmStatus update_bit(Pcm *pcm,uint16_t address,uint8_t clear,uint8_t set)
{
    uint8_t old;
    F_RUN(pcm_read8(pcm,address,&old));
    return pcm_write8(pcm,address,(uint8_t)((old&~clear)|set));
}
PcmStatus pcm_fuel_ignition_precheck(Pcm *pcm)
{
    if (pcm==NULL) return PCM_BAD_CONFIGURATION;
    uint16_t elapsed;
    uint8_t flags;
    F_RUN(pcm_read16(pcm,0x027e,&elapsed));
    F_RUN(pcm_read8(pcm,0x0044,&flags));
    if (flags&0x10u) { /* 7D4E: ignition-present source bit. */
        if (elapsed>=8u) {
            F_RUN(update_bit(pcm,0x0004,0x83u,0));
            F_RUN(update_bit(pcm,0x0019,0x40u,0));
            F_RUN(update_bit(pcm,0x0019,0x20u,0));
            F_RUN(pcm_write16(pcm,0x00fd,0));
            F_RUN(pcm_write16(pcm,0x024c,0));
            F_RUN(pcm_write8(pcm,0x0062,0));
            F_RUN(pcm_write8(pcm,0x02cd,0));
            F_RUN(pcm_write8(pcm,0x02ce,0));
            F_RUN(pcm_write8(pcm,0x0268,0));
            F_RUN(update_bit(pcm,0x0051,0,0x08u));
            F_RUN(update_bit(pcm,0x0086,0x08u,0));
            F_RUN(update_bit(pcm,0x004f,0x80u,0));
            F_RUN(update_bit(pcm,0x004f,0x10u,0));
            F_RUN(update_bit(pcm,0x0004,0x08u,0));
            uint16_t limit;
            F_RUN(pcm_read16(pcm,0x4009,&limit));
            if (elapsed>=limit) {
                /* 7D86..7D8E writes $08 to $3039, TAPs CCR=$50 and
                 * enters a nonreturning trap. A host return is a boundary. */
                F_RUN(pcm_write8(pcm,0x3039,0x08u));
                F_RUN(pcm_mask_irq(pcm,true));
                return PCM_HALT_BOUNDARY;
            }
        }
    } else { /* 7D90: ignition absent; reset off-history once. */
        F_RUN(pcm_read8(pcm,0x0051,&flags));
        if (flags&0x08u) {
            F_RUN(update_bit(pcm,0x0051,0x08u,0));
            F_RUN(update_bit(pcm,0x0046,0x80u,0));
            F_RUN(update_bit(pcm,0x0044,0x08u,0));
            F_RUN(update_bit(pcm,0x003e,0x08u,0));
            F_RUN(pcm_write8(pcm,0x0223,0));
            F_RUN(pcm_write8(pcm,0x027d,0));
        }
        F_RUN(update_bit(pcm,0x0086,0,0x08u));
        elapsed=0xffffu; /* 7DAA/7DAD makes the increment wrap to zero. */
    }
    F_RUN(pcm_write16(pcm,0x027e,(uint16_t)(elapsed+1u)));
    return pcm_write8(pcm,PCM_COPRST,0x55u); /* 7DB1..7DB5: only $55. */
}
