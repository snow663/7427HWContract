#include "resident_input_private_3.h"

PcmStatus pcm_resident_input_b089(Pcm *pcm)
{
    uint8_t a,b;
    bool fault,enabled;
    SYS_RUN(pcm_resident_diag_e8c8(pcm));
    SYS_RUN(pcm_resident_diag_eccc(pcm));
    SYS_RUN(pcm_resident_fault_e6f5(pcm));
    SYS_RUN(test(pcm,0x98,4,&fault));
    if(fault) SYS_RUN(pcm_write8(pcm,0xa2,0x88));
    SYS_RUN(pcm_read8(pcm,0x9f,&a));
    SYS_RUN(test(pcm,0x5b32,0x20,&enabled));
    if(enabled) {
        SYS_RUN(test(pcm,0x1d,0x20,&fault));
        if(fault) {
            SYS_RUN(pcm_write8(pcm,0x9f,(a&0xf0u)|9u));
            goto diagnostics;
        }
    }
    if(a&4u) {
        SYS_RUN(test(pcm,0x98,4,&fault));
        if(!fault) {
            SYS_RUN(pcm_read8(pcm,0x5d0f,&b));
            fault=b!=0;
        }
        SYS_RUN(pcm_write8(pcm,0x9f,fault?(uint8_t)(a^5u):a));
    }
diagnostics:
    SYS_RUN(pcm_resident_diag_e7c7(pcm));
    SYS_RUN(pcm_resident_diag_e808(pcm));
    SYS_RUN(pcm_resident_fault_e5cf(pcm));
    SYS_RUN(pcm_resident_diag_ebc0(pcm));
    SYS_RUN(test(pcm,0x400f,0x80,&enabled));
    if(!enabled) SYS_RUN(pcm_resident_diag_e847(pcm));
    SYS_RUN(pcm_resident_diag_ef2b(pcm));
    SYS_RUN(pcm_resident_diag_eb81(pcm));
    SYS_RUN(pcm_resident_fault_e60b(pcm));
    /* E6E4 is literal RTS. */
    return pcm_resident_fault_e5f1(pcm);
}
