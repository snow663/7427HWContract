#include "service_internal.h"
/*F739..F769. Edge latches set only after completed clear; failed stores retain prefix. */
PcmStatus pcm_service_clear(Pcm *pcm)
{
    bool requested=pcm->serial.clear_engine;
    if (!requested && pcm->runtime.engine_service) {
        uint8_t flags;SVC_RUN(pcm_serial_memory_read8(pcm,0x391,&flags));requested=(flags&0x40u)!=0;
    }
    if (requested) {
        if (!(pcm->serial.clear_edges&0x80u)) {
            SVC_RUN(pcm_diagnostic_clear_engine(pcm));pcm->serial.clear_edges|=0x80;
        }
    } else pcm->serial.clear_edges&=0x7fu;
    if (pcm->serial.clear_transmission) {
        if (!(pcm->serial.clear_edges&0x40u)) {
            SVC_RUN(pcm_diagnostic_clear_transmission(pcm));pcm->serial.clear_edges|=0x40;
        }
    } else pcm->serial.clear_edges&=0xbfu;
    return PCM_OK;
}
