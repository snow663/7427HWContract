/* The actual scheduler dispatch and resident callees, with separate named
 * owners and backing RAM. Stock replay supplies each initial byte. */
#include "calibration.h"
#include "control.h"
#include "fuel.h"
#include "scheduler.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(expr) do { if (!(expr)) { fprintf(stderr, "slots 05/0A line %d: %s\n", __LINE__, #expr); exit(3); } } while (0)

typedef struct { char kind; uint16_t address, value; } Event;
static struct {
    Pcm pcm;
    PcmPlatform platform;
    PcmCalibration cal;
    uint8_t mem[65536];
    Event events[4096];
    unsigned count, fail, change;
    bool injected;
} f;
static uint8_t image[65536];

static uint16_t word(uint16_t a)
{
    return (uint16_t)((uint16_t)f.mem[a] * 256u + f.mem[(uint16_t)(a + 1u)]);
}

static PcmStatus event(char kind, uint16_t address, uint16_t value)
{
    CHECK(f.count < sizeof(f.events) / sizeof(f.events[0]));
    f.events[f.count++] = (Event){kind, address, value};
    return f.count == f.fail ? PCM_NO_HARDWARE : PCM_OK;
}

static PcmStatus read8(void *ctx, uint16_t a, uint8_t *out)
{
    (void)ctx;
    uint8_t value = f.mem[a];
    PcmStatus s = event('r', a, value);
    if (s != PCM_OK) return s;
    *out = value;
    if (f.change == 1 && a == 0x4091) ++f.mem[a];       /* Two stride reads in F4DE. */
    if (f.change == 2 && a == 0x01d8) ++f.mem[a];       /* CMPB then INC on live RAM. */
    if (f.change == 3 && a == 0x0128) f.mem[a] ^= 15;   /* CMPA then LDAA. */
    if (f.change == 4 && a == 0x6aec) {
        f.mem[0x89] ^= 0x40;
        f.pcm.transmission.range_context = f.mem[0x89];
    }
    return PCM_OK;
}

static PcmStatus read16(void *ctx, uint16_t a, uint16_t *out)
{
    (void)ctx;
    uint16_t value = word(a);
    PcmStatus s = event('R', a, value);
    if (s == PCM_OK) {
        *out = value;
        if (f.change == 5 && a >= 0x4036 && a <= 0x40ff) f.mem[a] ^= 0x37;
    }
    return s;
}

static PcmStatus write8(void *ctx, uint16_t a, uint8_t value)
{
    (void)ctx;
    PcmStatus s = event('w', a, value);
    if (s != PCM_OK) return s;
    f.mem[a] = value;
    if (f.change == 6 && a == 0x01d6 && !f.injected) {
        f.injected = true;
        f.pcm.iac.runtime_high ^= 0xf0;
        f.mem[0x0232] ^= 0xf0;
    }
    if (f.change == 7 && a == 0x52) f.cal.mode_f ^= 0x40;
    if (f.change == 8 && a == 0x7c) f.pcm.iac.runtime_high ^= 0xf0;
    return PCM_OK;
}

static PcmStatus write16(void *ctx, uint16_t a, uint16_t value)
{
    (void)ctx;
    PcmStatus s = event('W', a, value);
    if (s == PCM_OK) {
        f.mem[a] = (uint8_t)(value >> 8);
        f.mem[(uint16_t)(a + 1u)] = (uint8_t)value;
    }
    return s;
}

static void setup(void)
{
    memset(&f, 0, sizeof(f));
    memcpy(f.mem, image, sizeof(image));
    f.platform.read8 = read8;
    f.platform.read16 = read16;
    f.platform.write8 = write8;
    f.platform.write16 = write16;
    f.pcm.platform = &f.platform;
    f.cal = pcm_reference_scheduler_calibration;
    f.pcm.calibration = &f.cal;
}

static void seed(void)
{
    const uint8_t *m = f.mem;
    f.pcm.scheduler.phase = m[2];
    f.cal.reference.mode_c = m[0x400c];
    f.cal.reference.mode_e = m[0x400e];
    f.cal.mode_f = m[0x400f];
    f.pcm.runtime.spark_running = (m[0x4f] & 0x80u) != 0;
    f.pcm.reference.throttle = m[0x1d9];
    f.pcm.reference.rpm_coordinate = m[0x62];
    f.pcm.iac.runtime_high = m[0x232];
    f.pcm.fuel.commanded_afr = m[0x24a];
    f.pcm.io.coolant_context = m[0x3e];
    f.pcm.fuel.output_rich_cap = (m[0x52] & 0x40u) != 0;
    f.pcm.io.coolant_conversion = m[0xa8];
    f.pcm.iac.gear_status = m[0xa2];
    f.pcm.io.brake_active = (m[0x9c] & 1u) != 0;
    f.pcm.spark.map_fault = (m[0x18] & 0x10u) != 0;
    f.pcm.fuel.oxygen_idle_fault = (m[0x18] & 0x20u) != 0;
    f.pcm.transmission.tcc_state = m[0x8b];
    f.pcm.transmission.tcc_flags = m[0x8a];
    f.pcm.transmission.tcc_command = word(0x126);
    f.pcm.transmission.tcc_lower_limit = word(0x12b);
    f.pcm.transmission.range_context = m[0x89];
    f.pcm.transmission.service_tcc = m[0x10a];
    f.pcm.spark.load_coordinate = m[0x1c0];
    f.pcm.reference.coolant = m[6];
    f.pcm.scheduler.run_counter = word(0xfd);
    f.pcm.runtime.deceleration_fuel_cut = (m[0x46] & 8u) != 0;
    f.pcm.spark.vehicle_speed_high = m[0x284];
    f.pcm.spark.density = word(0x257);
    f.pcm.iac.blm_cell_index = m[0x247];
    f.pcm.spark.vacuum = m[0x1c9];
    f.pcm.fuel.map_acceleration = (m[5] & 0x80u) != 0;
    f.pcm.fuel.tps_acceleration = (m[5] & 0x40u) != 0;
    f.pcm.fuel.integrator = m[0x20f];
}

static void emit(PcmStatus status)
{
    /* Each typed consumer is compared independently from its backing write. */
    printf("%u %u %u %u %u %u %u ", (unsigned)status, (unsigned)f.pcm.fuel.output_rich_cap,
           (unsigned)f.pcm.transmission.tcc_state, (unsigned)f.pcm.transmission.tcc_flags,
           (unsigned)f.pcm.transmission.tcc_command, (unsigned)f.pcm.transmission.tcc_lower_limit,
           (unsigned)f.pcm.transmission.range_context);
    f.mem[2] = f.pcm.scheduler.phase;
    f.mem[0x232] = f.pcm.iac.runtime_high;
    for (unsigned i = 0; i < 0x350; ++i) printf("%02x", (unsigned)f.mem[i]);
    printf(" %02x", (unsigned)f.mem[0x84c]);
    for (unsigned i = 0; i < f.count; ++i)
        printf(" %c%04x%04x", f.events[i].kind, (unsigned)f.events[i].address, (unsigned)f.events[i].value);
    putchar('\n');
}

static void contracts(void)
{
    setup();
    f.pcm.scheduler.phase = 0x1a;
    f.pcm.platform = NULL;
    CHECK(pcm_dispatch_slot(&f.pcm) == PCM_OK && f.count == 0);
    f.pcm.platform = &f.platform;
    f.pcm.scheduler.phase = 10;
    f.pcm.reference.coolant = 100;
    f.pcm.runtime.deceleration_fuel_cut = true;
    f.mem[0x1d7] = 77;
    f.mem[0x1d8] = 88;
    f.mem[0x41] = 0x21;
    CHECK(pcm_dispatch_slot(&f.pcm) == PCM_OK);
    CHECK(f.mem[0x1d6] == 255 && f.mem[0x1d7] == 77 && f.mem[0x1d8] == 88 && f.mem[0x41] == 0xa1);

    setup();
    f.pcm.scheduler.phase = 5;
    f.pcm.runtime.spark_running = true;
    f.pcm.io.coolant_context = 0x80;
    f.mem[0x78] = 150;
    f.mem[0x52] = 0x80;
    f.pcm.transmission.service_tcc = 100;
    f.pcm.transmission.tcc_state = 0x08;
    f.pcm.transmission.tcc_flags = 0x80;
    CHECK(pcm_dispatch_slot(&f.pcm) == PCM_OK);
    CHECK(f.mem[0x52] == 0xc0 && f.pcm.fuel.output_rich_cap);
    CHECK(word(0x126) == 65200 && f.pcm.transmission.tcc_command == 65200);
    CHECK(f.pcm.transmission.tcc_flags == 0x94 && f.mem[0x8a] == 0x94);
    CHECK(pcm_transmission_outputs(&f.pcm) == PCM_OK);
    CHECK(word(0x306a) == 0x7ffe && (f.pcm.transmission.tcc_state & 1u));
    f.pcm.fuel.commanded_afr = 255;
    CHECK(pcm_fuel_afr_finish(&f.pcm) == PCM_OK);
    CHECK(f.pcm.fuel.published_afr == f.cal.mixture->output_rich_limit[0]);
    /* A single live fault bypasses the MAP limit with the full reaction mask.
     * The independent raw byte is deliberately clear in this host handoff. */
    setup();
    f.pcm.scheduler.phase = 21;
    f.pcm.fuel.oxygen_idle_fault = true;
    f.mem[0x5b2d] = 0x30;
    f.mem[0x6aed] = 200;
    f.mem[0x7f] = 1;
    f.mem[0xc2d8] = 0x50;
    CHECK(pcm_dispatch_slot(&f.pcm) == PCM_OK && (f.pcm.transmission.tcc_state & 6u) == 4u);
    f.mem[0x5b2d] = 0x20;
    CHECK(pcm_dispatch_slot(&f.pcm) == PCM_OK && (f.pcm.transmission.tcc_state & 6u) == 2u);
    puts("Slots 05/0A purge, fuel AFR and TCC handoff contracts passed.");
}

int main(int argc, char **argv)
{
    CHECK(argc == 2);
    if (strcmp(argv[1], "--contracts") == 0) { contracts(); return 0; }
    FILE *file = fopen(argv[1], "rb");
    CHECK(file && fread(image, 1, sizeof(image), file) == sizeof(image) && fclose(file) == 0);
    unsigned passes, joined, fail, change, count;
    while (scanf("%u %u %u %u %u", &passes, &joined, &fail, &change, &count) == 5) {
        setup();
        for (unsigned i = 0; i < count; ++i) {
            unsigned a, b;
            CHECK(scanf("%u %u", &a, &b) == 2 && a <= 65535u && b < 256u);
            f.mem[a] = (uint8_t)b;
        }
        seed();
        f.fail = fail;
        f.change = change;
        PcmStatus status = PCM_OK;
        uint8_t phase = f.pcm.scheduler.phase;
        for (unsigned i = 0; i < passes && status == PCM_OK; ++i) {
            f.pcm.scheduler.phase = phase;
            status = pcm_dispatch_slot(&f.pcm);
            if (joined && status == PCM_OK) {
                f.pcm.scheduler.phase = (uint8_t)(phase + 5u);
                status = pcm_dispatch_slot(&f.pcm);
            }
            phase = (uint8_t)((phase + 16u) % 160u);
        }
        emit(status);
    }
    return ferror(stdin) ? 2 : 0;
}
