#ifndef PCM_SERIAL_INTERNAL_H
#define PCM_SERIAL_INTERNAL_H
#include "serial.h"
#include "hardware.h"
#define SER_RUN(call) do { PcmStatus ser_result=(call); if (ser_result!=PCM_OK) return ser_result; } while (0)
static inline bool ser_addressed(const Pcm *pcm) { return (pcm->serial.sessions&3u)!=0; }
/* Private typed bindings prevent a second owner for the serial RAM image. */
static inline bool ser_get(const Pcm *pcm,uint16_t a,uint8_t *out)
{
    if (a>=0x36c && a<=0x38d) { *out=pcm->serial.receive[a-0x36c];return true; }
    switch (a) {
    case 0x3b:*out=(uint8_t)((pcm->serial.clear_transmission?1:0)|(pcm->serial.clear_engine?2:0)|
        (pcm->runtime.monitor_freeze?4:0)|(pcm->runtime.transmission_service?8:0)|(pcm->runtime.engine_service?16:0)|
        (pcm->serial.deferred?32:0)|(pcm->serial.busy?64:0)|(pcm->serial.companion_pending?128:0));return true;
    case 0x42:*out=pcm->serial.sessions;return true;
    case 0x45:*out=pcm->serial.clear_edges;return true;
    case 0x360:*out=pcm->serial.count;return true;
    case 0x361:*out=pcm->serial.checksum;return true;
    case 0x362:*out=(uint8_t)(pcm->serial.descriptor>>8);return true;
    case 0x363:*out=(uint8_t)pcm->serial.descriptor;return true;
    case 0x364:*out=pcm->serial.last_id;return true;
    case 0x365:*out=pcm->serial.length;return true;
    case 0x366:*out=pcm->serial.companion;return true;
    case 0x367:*out=pcm->serial.receive_age;return true;
    case 0x368:*out=(uint8_t)(pcm->serial.service_age>>8);return true;
    case 0x369:*out=(uint8_t)pcm->serial.service_age;return true;
    case 0x36a:*out=(uint8_t)(pcm->serial.service_expiry>>8);return true;
    case 0x36b:*out=(uint8_t)pcm->serial.service_expiry;return true;
    case 0x38e:*out=pcm->serial.engine_command;return true;
    case 0x399:*out=pcm->serial.transmission_command;return true;
    default:return false;
    }
}
/* Common named RAM owner: called by direct SCI/ALDL access AND the opt-in
 * physical address bridge. Exactly one writer owns each serial field. */
static inline bool ser_put(Pcm *pcm,uint16_t a,uint8_t v)
{
    if (a>=0x36c && a<=0x38d) { pcm->serial.receive[a-0x36c]=v;return true; }
    switch (a) {
    case 0x3b:pcm->serial.clear_transmission=(v&1u)!=0;pcm->serial.clear_engine=(v&2u)!=0;
        pcm->runtime.monitor_freeze=(v&4u)!=0;pcm->runtime.transmission_service=(v&8u)!=0;pcm->runtime.engine_service=(v&16u)!=0;
        pcm->serial.deferred=(v&32u)!=0;pcm->serial.busy=(v&64u)!=0;pcm->serial.companion_pending=(v&128u)!=0;return true;
    case 0x42:pcm->serial.sessions=v;return true;
    case 0x45:pcm->serial.clear_edges=v;return true;
    case 0x360:pcm->serial.count=v;return true;
    case 0x361:pcm->serial.checksum=v;return true;
    case 0x362:pcm->serial.descriptor=(uint16_t)((uint16_t)v*256u+(pcm->serial.descriptor&255u));return true;
    case 0x363:pcm->serial.descriptor=(uint16_t)((pcm->serial.descriptor&0xff00u)|v);return true;
    case 0x364:pcm->serial.last_id=v;return true;
    case 0x365:pcm->serial.length=v;return true;
    case 0x366:pcm->serial.companion=v;return true;
    case 0x367:pcm->serial.receive_age=v;return true;
    case 0x368:pcm->serial.service_age=(uint16_t)((uint16_t)v*256u+(pcm->serial.service_age&255u));return true;
    case 0x369:pcm->serial.service_age=(uint16_t)((pcm->serial.service_age&0xff00u)|v);return true;
    case 0x36a:pcm->serial.service_expiry=(uint16_t)((uint16_t)v*256u+(pcm->serial.service_expiry&255u));return true;
    case 0x36b:pcm->serial.service_expiry=(uint16_t)((pcm->serial.service_expiry&0xff00u)|v);return true;
    case 0x38e:pcm->serial.engine_command=v;return true;
    case 0x399:pcm->serial.transmission_command=v;return true;
    default:return false;
    }
}
#endif
