#include "interrupts.h"
#include "serial.h"
#define RUN(call) do { PcmStatus status=(call); if (status!=PCM_OK) return status; } while (0)

/* 7959..7979, excluding TSX/PSHX/PULX, LDS and the caller's interrupt frame.
 * The target shim supplies the X value obtained from TSX (SP+1) after CLI.
 * This routine performs the literal software tests and ordered byte RMWs;
 * a true recovery result requires the target to execute LDS #$03F6 before
 * resuming at 797A. It must not alter the native host C stack. */
PcmStatus pcm_timer_stack_guard(Pcm *pcm,uint16_t stack_x,bool *needs_reset)
{
    if (needs_reset==NULL) return PCM_BAD_CONFIGURATION;
    *needs_reset=false;
    uint8_t flags;
    RUN(pcm_serial_memory_read8(pcm,0x004f,&flags)); /*795C BRSET bit2 */
    bool overrun=(flags&0x04u)!=0;
    bool invalid=stack_x<0x03b0u ||
                 stack_x>(overrun?0x03eeu:0x03f7u);
    if (!invalid) return PCM_OK;
    uint8_t faults;
    RUN(pcm_serial_memory_read8(pcm,0x003a,&faults));
    RUN(pcm_serial_memory_write8(pcm,0x003a,(uint8_t)(faults|0x08u)));
    /* 7974 is a fresh RMW, not an edit of the earlier 004F snapshot. */
    RUN(pcm_serial_memory_read8(pcm,0x004f,&flags));
    RUN(pcm_serial_memory_write8(pcm,0x004f,(uint8_t)(flags&~0x04u)));
    *needs_reset=true; /* LDS #$03F6 belongs to the target entry shim. */
    return PCM_OK;
}
