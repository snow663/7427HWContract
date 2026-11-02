#include "control.h"
#include "hardware.h"
#include "reference_math.h"
static uint16_t fraction(uint16_t numerator,uint16_t denominator)
{ return numerator>=denominator?UINT16_MAX:(uint16_t)(((uint32_t)numerator<<16)/denominator); }
/* ACA7..ADA9. Retain the low quotient byte and wrapped1.5*delta.
 * Gear5 is a real loop exit rather than an added fourth-gear clamp. */
PcmStatus pcm_shift_lamp(Pcm *pcm)
{
    if (pcm->calibration==NULL) return PCM_BAD_CONFIGURATION;
    if (!(pcm->calibration->reference.mode_e&4u)) return PCM_OK;
    if (pcm->runtime.diagnostic_switch && !pcm->runtime.spark_running) goto on;
    if (pcm->runtime.engine_service && pcm->transmission.shift_service_enable) {
        if (pcm->transmission.shift_service_value) goto on;
        goto off;
    }
    uint16_t counter;
    PcmStatus result=pcm_read16(pcm,PCM_SHIFT_COUNTER,&counter);
    if (result!=PCM_OK) return result;
    pcm->transmission.shift_delta=(uint16_t)(counter-pcm->transmission.shift_counter);
    pcm->transmission.shift_counter=counter;
    if (pcm->calibration->transmission==NULL) return PCM_BAD_CONFIGURATION;
    const PcmTransmissionCalibration *cal=pcm->calibration->transmission;
    if (pcm->reference.coolant<=cal->shift_coolant ||
        cal->shift_throttle[pcm->transmission.shift_gear>2u]>pcm->reference.throttle ||
        pcm->spark.vehicle_speed_high<5u) goto reload;
    if (pcm->reference.rpm_coordinate>cal->shift_rpm_max) goto on;
    if (pcm->reference.rpm_coordinate<40u) goto reload;
    pcm->transmission.shift_gear=1;
    uint16_t delta=pcm->transmission.shift_delta;
    uint16_t scaled=(uint16_t)(delta+(delta>>1));
    uint16_t numerator=fraction(15,pcm->spark.period_basis);
    uint8_t ratio=(uint8_t)(scaled?numerator/scaled:UINT16_MAX);
    pcm->transmission.shift_ratio=ratio;
    unsigned index=0;
    while (ratio<cal->shift_ratio[index]) {
        ++pcm->transmission.shift_gear;++index;
        if (pcm->transmission.shift_gear>=5u) goto reload;
    }
    if (pcm->reference.rpm_coordinate<=cal->shift_rpm[index]) goto reload;
    uint32_t product=2u*(uint32_t)cal->shift_throttle_gain[index]*pcm->reference.throttle+128u;
    uint8_t threshold=product>UINT16_MAX?255u:(uint8_t)(product>>8);
    unsigned offset=pcm->transmission.shift_gear>2u?22u:0u;
    if (!pcm->transmission.shift_lamp) offset+=11;
    uint8_t rpm=pcm->reference.rpm_coordinate;
    if (rpm>200u) rpm=200;
    uint8_t rpm_term=pcm_lookup16((uint8_t)(rpm-40u),cal->shift_curves+offset);
    uint8_t baro=pcm->spark.barometric_pressure;
    uint8_t baro_term=pcm_lookup16(baro<96u?0:(uint8_t)(baro-96u),cal->shift_curves+44);
    product=2u*(uint32_t)rpm_term*baro_term;
    uint8_t available=product>UINT16_MAX?255u:(uint8_t)(product>>8);
    if (available<threshold) goto reload;
    if (!pcm->transmission.shift_hold) goto on;
    --pcm->transmission.shift_hold;goto off;
reload:
    pcm->transmission.shift_hold=cal->shift_reload[pcm->transmission.shift_gear>2u];
off:
    pcm->transmission.shift_lamp=false;return PCM_OK;
on:
    pcm->transmission.shift_lamp=true;return PCM_OK;
}
