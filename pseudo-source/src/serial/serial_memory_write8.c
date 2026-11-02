#include "serial_internal.h"
/* Commit only after a successful foreign write. Shared controller/service bytes
 * outside the owned serial area are bound by the address-space provider. */
PcmStatus pcm_serial_memory_write8(Pcm *pcm,uint16_t a,uint8_t v)
{
    if (a>=0x36c && a<=0x38d) { pcm->serial.receive[a-0x36c]=v;return PCM_OK; }
    switch (a) {
    case 0x3b:pcm->serial.clear_transmission=(v&1u)!=0;pcm->serial.clear_engine=(v&2u)!=0;
        pcm->runtime.monitor_freeze=(v&4u)!=0;pcm->runtime.transmission_service=(v&8u)!=0;pcm->runtime.engine_service=(v&16u)!=0;
        pcm->serial.deferred=(v&32u)!=0;pcm->serial.busy=(v&64u)!=0;pcm->serial.companion_pending=(v&128u)!=0;return PCM_OK;
    case 0x42:pcm->serial.sessions=v;return PCM_OK;
    case 0x45:pcm->serial.clear_edges=v;return PCM_OK;
    case 0x360:pcm->serial.count=v;return PCM_OK;
    case 0x361:pcm->serial.checksum=v;return PCM_OK;
    case 0x362:pcm->serial.descriptor=(uint16_t)((uint16_t)v*256u+(pcm->serial.descriptor&255u));return PCM_OK;
    case 0x363:pcm->serial.descriptor=(uint16_t)((pcm->serial.descriptor&0xff00u)|v);return PCM_OK;
    case 0x364:pcm->serial.last_id=v;return PCM_OK;
    case 0x365:pcm->serial.length=v;return PCM_OK;
    case 0x366:pcm->serial.companion=v;return PCM_OK;
    case 0x367:pcm->serial.receive_age=v;return PCM_OK;
    case 0x368:pcm->serial.service_age=(uint16_t)((uint16_t)v*256u+(pcm->serial.service_age&255u));return PCM_OK;
    case 0x369:pcm->serial.service_age=(uint16_t)((pcm->serial.service_age&0xff00u)|v);return PCM_OK;
    case 0x36a:pcm->serial.service_expiry=(uint16_t)((uint16_t)v*256u+(pcm->serial.service_expiry&255u));return PCM_OK;
    case 0x36b:pcm->serial.service_expiry=(uint16_t)((pcm->serial.service_expiry&0xff00u)|v);return PCM_OK;
    case 0x38e:pcm->serial.engine_command=v;return PCM_OK;
    case 0x399:pcm->serial.transmission_command=v;return PCM_OK;
    default:return pcm_write8(pcm,a,v);
    }
}
