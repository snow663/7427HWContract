/* Compare the real dispatch entries with a logical bus and an ADC whose
 * ready poll and result can be controlled independently. */
#include "calibration.h"
#include "hardware.h"
#include "scheduler.h"
#include "board_io.h"
#include "fuel.h"
#include "control.h"
#include "iac.h"
#include "service.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(x) do { if (!(x)) { fprintf(stderr, "slots 0C/0D line %d: %s\n", __LINE__, #x); exit(3); } } while (0)
typedef struct { char kind; uint16_t address, value; } Event;
static struct {
    Pcm pcm;
    PcmPlatform platform;
    PcmCalibration cal;
    PcmAirCalibration air;
    PcmFeedbackCalibration feedback;
    uint8_t mem[65536];
    Event events[65536]; /* Holds the complete three-code flash sequence. */
    unsigned used, fail, action, ready, polls;
    bool masked, changed;
} f;
static uint8_t image[65536];

static uint16_t word(uint16_t a)
{
    return (uint16_t)((uint16_t)f.mem[a] * 256u + f.mem[(uint16_t)(a + 1u)]);
}
static uint8_t bit(uint8_t v, uint8_t mask, bool set)
{
    return set ? (uint8_t)(v | mask) : (uint8_t)(v & (uint8_t)~mask);
}
static PcmStatus event(char kind, uint16_t a, uint16_t v)
{
    CHECK(f.used < sizeof(f.events)/sizeof(f.events[0]));
    f.events[f.used++] = (Event){kind, a, v};
    return f.used == f.fail ? PCM_NO_HARDWARE : PCM_OK;
}
static PcmStatus read8(void *ctx, uint16_t a, uint8_t *out)
{
    (void)ctx;
    uint8_t v = f.mem[a];
    /* Native ADC and MAT routines publish these bits before diagnostic logging. */
    if (a == 0x17) v = bit(bit(v, 0x40, f.pcm.io.mat_low_fault), 0x10, f.pcm.io.mat_high_fault);
    if (a == 0x1a) v = bit(v, 2, f.pcm.runtime.adc_timeout);
    if (a == 0x3a) v = bit(v, 1, f.pcm.runtime.adc_fault);
    if (a == PCM_ADCTL) {
        ++f.polls;
        if (f.ready && f.polls >= f.ready) v |= 0x80u;
    }
    PcmStatus result = event('r', a, v);
    if (result != PCM_OK) return result;
    *out = v;
    if (f.action == 1 && a == 0x4e38) f.mem[0x021c]++;
    if (f.action == 2 && a == 0x015f) f.mem[a]++;
    if (f.action == 3 && a == 0x5b06) f.mem[0x5c] ^= 0x20;
    return PCM_OK;
}
static PcmStatus read16(void *ctx, uint16_t a, uint16_t *out)
{
    (void)ctx;
    uint16_t v = word(a);
    PcmStatus result = event('R', a, v);
    if (result == PCM_OK) *out = v;
    return result;
}
static PcmStatus write8(void *ctx, uint16_t a, uint8_t v)
{
    (void)ctx;
    PcmStatus result = event('w', a, v);
    if (result != PCM_OK) return result;
    f.mem[a] = v;
    if (a == PCM_ADCTL) f.polls = 0;
    if (f.action == 4 && a == 0x0223) f.mem[0x70] ^= 8;
    if (f.action == 5 && a == 0x022b) f.mem[0x58] ^= 1;
    return PCM_OK;
}
static PcmStatus write16(void *ctx, uint16_t a, uint16_t v)
{
    (void)ctx;
    PcmStatus result = event('W', a, v);
    if (result == PCM_OK) {
        f.mem[a] = (uint8_t)(v >> 8);
        f.mem[(uint16_t)(a+1u)] = (uint8_t)v;
        if (f.action == 6 && a == 0x3fda) f.pcm.runtime.engine_service = true;
    }
    return result;
}
static PcmStatus mask_irq(void *ctx, bool masked)
{
    (void)ctx;
    PcmStatus result = event('m', 0, (uint16_t)masked);
    if (result == PCM_OK) {
        f.masked = masked;
        if (f.action == 7 && !masked && !f.changed) {
            f.changed = true;
            f.mem[PCM_ADR4] ^= 0xe7;
            f.pcm.transmission.output_shadow ^= 0x20;
            f.mem[0x4c] ^= 0x20;
        }
    }
    return result;
}
static PcmStatus delay(void *ctx, uint16_t cycles)
{
    (void)ctx;
    return event('d', 0, cycles);
}
static void setup(void)
{
    memset(&f, 0, sizeof(f));
    memcpy(f.mem, image, sizeof(image));
    f.platform.read8 = read8;
    f.platform.read16 = read16;
    f.platform.write8 = write8;
    f.platform.write16 = write16;
    f.platform.mask_irq = mask_irq;
    f.platform.delay_cycles = delay;
    f.pcm.platform = &f.platform;
    f.cal = pcm_reference_scheduler_calibration;
    f.air = *f.cal.air;
    f.feedback = *f.cal.feedback;
    f.cal.air = &f.air;
    f.cal.feedback = &f.feedback;
    f.pcm.calibration = &f.cal;
}
static void seed(void)
{
    const uint8_t *m = f.mem;
    f.pcm.scheduler.phase = m[2];
    f.pcm.scheduler.run_counter = word(0xfd);
    f.pcm.reference.coolant = m[6];
    f.pcm.runtime.primary_faults = m[0x16];
    f.pcm.iac.input_fault = (m[0x17] & 128u) != 0;
    f.pcm.io.mat_low_fault = (m[0x17] & 64u) != 0;
    f.pcm.io.mat_high_fault = (m[0x17] & 16u) != 0;
    f.pcm.iac.learning_fault = (m[0x18] & 8u) != 0;
    f.pcm.iac.kicker_fault = (m[0x18] & 4u) != 0;
    f.pcm.spark.map_fault = (m[0x18] & 16u) != 0;
    f.pcm.fuel.oxygen_idle_fault = (m[0x18] & 32u) != 0;
    f.pcm.fuel.oxygen_fault_a = (m[0x19] & 4u) != 0;
    f.pcm.fuel.oxygen_fault_b = (m[0x19] & 8u) != 0;
    f.pcm.knock.sensor_fault = (m[0x19] & 16u) != 0;
    f.pcm.spark.est_fault = (m[0x19] & 32u) != 0;
    f.pcm.reference.bank_fault = (m[0x19] & 64u) != 0;
    f.pcm.runtime.adc_timeout = (m[0x1a] & 2u) != 0;
    f.pcm.runtime.special_fast_group = (m[0x1a] & 32u) != 0;
    f.pcm.transmission.fault_flags_primary = m[0x1c];
    f.pcm.transmission.fault_flags_secondary = m[0x1d];
    f.pcm.runtime.adc_fault = (m[0x3a] & 1u) != 0;
    f.pcm.runtime.engine_service = (m[0x3b] & 16u) != 0;
    f.pcm.fuel.authorized = (m[0x3d] & 2u) != 0;
    f.pcm.runtime.power_enrichment = (m[0x3d] & 32u) != 0;
    f.pcm.io.coolant_context = m[0x3e];
    f.pcm.io.ac_mirror = (m[0x41] & 16u) != 0;
    f.pcm.fuel.oxygen_changed = (m[0x43] & 16u) != 0;
    f.pcm.scheduler.epoch_toggle = (m[0x43] & 32u) != 0;
    f.pcm.runtime.first_conversion = (m[0x43] & 128u) != 0;
    f.pcm.runtime.output_override = (m[0x44] & 4u) != 0;
    f.pcm.reference.latch_inhibited = (m[0x44] & 16u) != 0;
    f.pcm.runtime.deceleration_fuel_cut = (m[0x46] & 8u) != 0;
    f.pcm.transmission.output_shadow = m[0x4c];
    f.pcm.spark.startup_gain_enabled = (m[0x4f] & 64u) != 0;
    f.pcm.runtime.spark_running = (m[0x4f] & 128u) != 0;
    f.pcm.fuel.idle_afr_ready = (m[0x50] & 2u) != 0;
    f.pcm.io.diagnostic_warm = (m[0x50] & 8u) != 0;
    f.pcm.runtime.diagnostic_switch = (m[0x50] & 16u) != 0;
    f.pcm.transmission.shift_lamp = (m[0x53] & 4u) != 0;
    f.pcm.spark.run_transition = (m[4] & 8u) != 0;
    f.pcm.spark.bypass_supervision = (m[4] & 128u) != 0;
    f.pcm.spark.rpm_low_coordinate = m[0x61];
    f.pcm.reference.rpm_coordinate = m[0x62];
    f.pcm.fuel.asynchronous_active = (m[0x6e] & 1u) != 0;
    f.pcm.spark.load_status = m[0x6f];
    f.pcm.fuel.alternate_interval = (m[0x70] & 4u) != 0;
    f.pcm.fuel.oxygen_notification = (m[0x71] & 4u) != 0;
    f.pcm.fuel.alternate_afr_limit = (m[0x72] & 64u) != 0;
    f.pcm.runtime.service_output_mirror = (m[0x72] & 128u) != 0;
    f.pcm.transmission.range_context = m[0x89];
    f.pcm.spark.battery_sample = m[0xa7];
    f.pcm.spark.map_filtered = m[0x1c6];
    f.pcm.spark.vacuum = m[0x1c9];
    f.pcm.fuel.raw_oxygen = m[0x1d5];
    f.pcm.reference.throttle = m[0x1d9];
    f.pcm.fuel.throttle_decel_filter = word(0x1de);
    f.pcm.spark.bypass_baseline = word(0x205);
    f.pcm.fuel.integrator = m[0x20f];
    f.pcm.io.mat_low_count = m[0x21d];
    f.pcm.io.mat_high_count = m[0x21e];
    f.pcm.io.egr_failure_count = m[0x223];
    f.pcm.spark.bypass_count = m[0x22c];
    f.pcm.spark.mat_sample = m[0x22f];
    f.pcm.io.mat_raw = m[0x230];
    f.pcm.iac.starting_coolant = m[0x282];
    f.pcm.spark.vehicle_speed_high = m[0x284];
    f.pcm.transmission.governor_integrator = word(0x288);
    memcpy((void *)f.pcm.fuel.blm_cells, m + 0x2b3, 21);
    f.pcm.spark.barometric_high = m[0x2f4];
    f.pcm.reference.map_sample = m[0x82e];
    f.pcm.transmission.shift_delta = word(0x849);
    f.pcm.io.mat_display = m[0x855];
    f.cal.reference.mode_b = m[0x400b];
    f.cal.reference.mode_c = m[0x400c];
    f.cal.mode_d = m[0x400d];
    f.cal.reference.mode_e = m[0x400e];
    f.cal.mode_f = m[0x400f];
    f.air.mat_runtime_limit = word(0x4e45);
    f.air.mat_options = m[0x5b01];
    f.air.mat_low_threshold = m[0x4e41]; f.air.mat_low_delay = m[0x4e42];
    f.air.mat_high_threshold = m[0x4e49]; f.air.mat_high_delay = m[0x4e4a];
    f.air.mat_speed_limit = m[0x4e47]; f.air.mat_default = m[0x4e48];
    memcpy(f.air.mat_curve, m + 0xfe45, sizeof(f.air.mat_curve));
    f.feedback.boot_maximum = m[0x48fd]; f.feedback.boot_minimum = m[0x48fe];
}
static void hex(const uint8_t *s, unsigned n)
{
    for (unsigned i = 0; i < n; ++i) printf("%02x", (unsigned)s[i]);
    putchar(' ');
}
static void emit(PcmStatus status)
{
    uint8_t *m = f.mem;
    uint8_t owners[] = {f.pcm.iac.starting_coolant, f.pcm.fuel.raw_oxygen, f.pcm.transmission.output_shadow,
        f.pcm.io.ac_mirror, f.pcm.transmission.shift_lamp, f.pcm.runtime.primary_faults, f.pcm.spark.load_status,
        f.pcm.runtime.service_output_mirror, f.pcm.fuel.oxygen_fault_a, f.pcm.fuel.oxygen_fault_b,
        f.pcm.fuel.oxygen_idle_fault, f.pcm.fuel.alternate_afr_limit, f.pcm.fuel.oxygen_notification,
        f.pcm.fuel.alternate_interval, f.pcm.fuel.asynchronous_active, f.pcm.io.egr_failure_count,
        f.pcm.spark.bypass_count, (uint8_t)(f.pcm.spark.bypass_baseline >> 8), (uint8_t)f.pcm.spark.bypass_baseline,
        f.pcm.spark.bypass_supervision, f.pcm.fuel.oxygen_changed};
    printf("%u %u ", (unsigned)status, (unsigned)f.masked);
    hex(owners, sizeof(owners));
    /* Reconstruct only native MAT/ADC/BLM fields and the injected service input. */
    m[2] = f.pcm.scheduler.phase;
    m[0x17] = bit(bit(m[0x17], 0x40, f.pcm.io.mat_low_fault), 0x10, f.pcm.io.mat_high_fault);
    m[0x1a] = bit(m[0x1a], 2, f.pcm.runtime.adc_timeout);
    m[0x3a] = bit(m[0x3a], 1, f.pcm.runtime.adc_fault);
    m[0x3b] = bit(m[0x3b], 16, f.pcm.runtime.engine_service);
    m[0x21d] = f.pcm.io.mat_low_count; m[0x21e] = f.pcm.io.mat_high_count;
    m[0x22f] = f.pcm.spark.mat_sample; m[0x230] = f.pcm.io.mat_raw; m[0x855] = f.pcm.io.mat_display;
    memcpy(m + 0x2b3, (const void *)f.pcm.fuel.blm_cells, 21);
    hex(m, 0x350); hex(m + 0x800, 0x100); hex(m + 0x3000, 0x70); hex(m + 0x3fc0, 0x40);
    for (unsigned i=0; i<f.used; ++i)
        printf("%c%04x%04x ", f.events[i].kind, (unsigned)f.events[i].address, (unsigned)f.events[i].value);
    putchar('\n');
}
static void contracts(void)
{
    setup();
    f.pcm.scheduler.phase = 12;
    f.pcm.reference.coolant = 165;
    f.mem[0x48be] = 127; f.mem[0x1d1] = 255;
    CHECK(pcm_dispatch_slot(&f.pcm) == PCM_OK && f.pcm.iac.starting_coolant == 165);
    CHECK(word(0x1d0) == 0x7f00 && f.pcm.fuel.raw_oxygen == 127);
    f.cal.reference.mode_c |= 0x80;
    f.pcm.scheduler.phase = 10;
    CHECK(pcm_dispatch_slot(&f.pcm) == PCM_OK && f.mem[0x1d6] == 255);
    f.pcm.runtime.spark_running = true;
    f.pcm.scheduler.phase = 13;
    f.ready = 1;
    CHECK(pcm_dispatch_slot(&f.pcm) == PCM_OK && word(0x3fd6) == 0xb7f8);

    /* A fault produced by MAT must seed the pending log immediately. */
    f.cal.reference.mode_b = 0;
    f.pcm.scheduler.run_counter = 100;
    f.air.mat_runtime_limit = 0; f.air.mat_options = 0x40;
    f.air.mat_low_threshold = 120; f.air.mat_low_delay = 1;
    f.pcm.io.mat_low_count = 2; f.mem[PCM_ADR4] = 255;
    f.mem[0x5b01] = 0x40;
    CHECK(pcm_dispatch_slot(&f.pcm) == PCM_OK && f.pcm.io.mat_low_fault);
    CHECK(f.mem[0x57] == 0x40);
    f.mem[0x5b0a] = 0x40;
    CHECK(pcm_dispatch_slot(&f.pcm) == PCM_OK && (f.mem[0x0c] & 0x40u));
    CHECK(f.pcm.runtime.service_output_mirror);
    CHECK(pcm_board_latch(&f.pcm) == PCM_OK && !(word(PCM_BOARD_CONTROL) & 8u));
    uint8_t checksum;
    CHECK(pcm_diagnostic_checksum(&f.pcm, &checksum) == PCM_OK && checksum == f.mem[0x15]);
    /* Both an IAC-native fault and an addressed transmission fault must
     * survive the nine-bank seed, even with independent backing storage. */
    setup();
    f.pcm.iac.context = 8;
    f.pcm.iac.rpm_error_filtered = 0xff00;
    f.pcm.iac.learning_count = 255;
    CHECK(pcm_iac_learning_diagnostic(&f.pcm) == PCM_OK && f.pcm.iac.learning_fault);
    f.mem[0x5b06] = 2; f.mem[0x8e] = 128; f.mem[0x5b8f] = 1;
    CHECK(pcm_diagnostic_current_error(&f.pcm) == PCM_OK && (f.mem[0x1c] & 2u));
    f.mem[0x5b02] = 8;
    f.pcm.scheduler.phase = 13; f.ready = 1;
    CHECK(pcm_dispatch_slot(&f.pcm) == PCM_OK);
    CHECK((f.mem[0x58] & 8u) && (f.mem[0x5c] & 2u));
    /* A service clear must reach native sources before 0D can reseed them.
     * Transmit the stock masks for these live banks. Engine clear retains
     * the transmission fault. Transmission clear retains pending candidates
     * until the next 0D intersection. */
    f.mem[0xf379] = 3; f.mem[0xf37d] = 255;
    CHECK(pcm_diagnostic_clear_engine(&f.pcm) == PCM_OK && !f.pcm.iac.learning_fault);
    CHECK(!(f.mem[0x58] & 8u) && (f.mem[0x5c] & 2u));
    CHECK(pcm_diagnostic_clear_transmission(&f.pcm) == PCM_OK);
    CHECK(!(f.mem[0x1c] & 2u) && (f.mem[0x5c] & 2u));
    CHECK(pcm_dispatch_slot(&f.pcm) == PCM_OK && !(f.mem[0x5c] & 2u));
    CHECK(pcm_dispatch_slot(&f.pcm) == PCM_OK && !(f.mem[0x58] & 8u));

    setup();
    f.pcm.iac.learning_fault = true;
    f.mem[0x18] = 8; f.mem[0xf379] = 3;
    /* Six preceding bank indices, then history, then the live read, mask
     * read and failing write. Only the successful retry clears the owner. */
    f.fail = 6*9 + 6;
    CHECK(pcm_diagnostic_clear_engine(&f.pcm) == PCM_NO_HARDWARE);
    CHECK(f.pcm.iac.learning_fault && f.mem[0x18] == 8);
    f.fail = 0;
    CHECK(pcm_diagnostic_clear_engine(&f.pcm) == PCM_OK && !f.pcm.iac.learning_fault);
    puts("Register refresh, purge, MAT, IAC, transmission fault log, clear and lamp handoffs passed.");
}
int main(int argc, char **argv)
{
    CHECK(argc == 2);
    if (!strcmp(argv[1], "--contracts")) { contracts(); return 0; }
    FILE *rom = fopen(argv[1], "rb");
    CHECK(rom && fread(image, 1, sizeof(image), rom) == sizeof(image) && fclose(rom) == 0);
    unsigned passes, joined, fail, action, ready, masked, n;
    while (scanf("%u %u %u %u %u %u %u", &passes, &joined, &fail, &action, &ready, &masked, &n) == 7) {
        setup();
        for (unsigned i=0; i<n; ++i) {
            unsigned a, v;
            CHECK(scanf("%u %u", &a, &v) == 2 && a < 65536 && v < 256);
            f.mem[a] = (uint8_t)v;
        }
        seed();
        f.fail = fail; f.action = action; f.ready = ready; f.masked = masked != 0;
        PcmStatus status = PCM_OK;
        uint8_t phase = f.pcm.scheduler.phase;
        for (unsigned i=0; i<passes && status==PCM_OK; ++i) {
            f.pcm.scheduler.phase = phase;
            status = pcm_dispatch_slot(&f.pcm);
            if (status == PCM_OK && joined) {
                f.pcm.scheduler.phase = (uint8_t)(phase+1u);
                status = pcm_dispatch_slot(&f.pcm);
            }
            phase = (uint8_t)((phase+16u)%160u);
        }
        emit(status);
    }
    return ferror(stdin) ? 2 : 0;
}
