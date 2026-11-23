/* Real slot 04 entry. Only named RAM/calibration views are seeded at entry.
 * The new logical bus transactions and mask edges remain observable in order. */
#include "calibration.h"
#include "control.h"
#include "fuel.h"
#include "scheduler.h"
#include "service.h"
#include "system.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(x) do { if (!(x)) { fprintf(stderr, "slot 04 line %d: %s\n", __LINE__, #x); exit(3); } } while (0)
typedef struct {
    char kind;
    uint16_t address, value;
} Event;

typedef struct {
    Pcm pcm;
    PcmPlatform platform;
    PcmCalibration cal;
    PcmAirCalibration air;
    PcmEnvironmentCalibration env;
    uint8_t mem[65536];
    Event events[3200];
    unsigned used, fail, action;
    bool masked, injected;
} Fixture;

static Fixture f;
static uint8_t image[65536];

static uint16_t word(const uint8_t *mem, uint16_t a)
{
    return (uint16_t)((uint16_t)mem[a] * 256u + mem[(uint16_t)(a + 1u)]);
}

static PcmStatus event(Fixture *v, char kind, uint16_t a, uint16_t value)
{
    CHECK(v->used < sizeof(v->events) / sizeof(v->events[0]));
    v->events[v->used++] = (Event){kind, a, value};
    return v->used == v->fail ? PCM_NO_HARDWARE : PCM_OK;
}

static PcmStatus read8(void *ctx, uint16_t a, uint8_t *out)
{
    Fixture *v = ctx;
    uint8_t byte = v->mem[a];
    PcmStatus s = event(v, 'r', a, byte);
    if (s != PCM_OK) return s;
    *out = byte;
    if (v->action == 1 && (a == 0x5d0b || a == 0x5d0c || a == 0x5b96 || a == 0x5b98)) v->mem[a] ^= 0x75;
    if (v->action == 2 && a == 0x5d36) v->mem[a] = (uint8_t)(byte + 80u);
    return PCM_OK;
}

static PcmStatus read16(void *ctx, uint16_t a, uint16_t *out)
{
    Fixture *v = ctx;
    uint16_t value = word(v->mem, a);
    PcmStatus s = event(v, 'R', a, value);
    if (s == PCM_OK) *out = value;
    return s;
}

static PcmStatus write8(void *ctx, uint16_t a, uint8_t byte)
{
    Fixture *v = ctx;
    PcmStatus s = event(v, 'w', a, byte);
    if (s != PCM_OK) return s;
    v->mem[a] = byte;
    if (v->action == 3 && a == 0x16f) v->pcm.scheduler.phase ^= 0x10;
    if (v->action == 4 && a == 0x17c) v->pcm.runtime.monitor_freeze = true;
    if (v->action == 6 && a == 0x6f && !v->injected) {
        v->injected = true;
        v->mem[a] ^= 0x08;
        v->pcm.spark.load_status ^= 0x08;
    }
    return PCM_OK;
}

static PcmStatus write16(void *ctx, uint16_t a, uint16_t value)
{
    Fixture *v = ctx;
    PcmStatus s = event(v, 'W', a, value);
    if (s == PCM_OK) {
        v->mem[a] = (uint8_t)(value >> 8);
        v->mem[(uint16_t)(a + 1u)] = (uint8_t)value;
    }
    return s;
}

static PcmStatus mask_irq(void *ctx, bool masked)
{
    Fixture *v = ctx;
    PcmStatus s = event(v, 'm', 0, masked);
    if (s != PCM_OK) return s;
    v->masked = masked;
    if (v->action == 5 && !masked && !v->injected) {
        v->injected = true;
        v->pcm.transmission.adaptive_flags |= 0x80u;
        v->mem[0x32b]++;
    }
    return PCM_OK;
}

static void configure(void)
{
    memset(&f, 0, sizeof(f));
    memcpy(f.mem, image, sizeof(image));
    f.platform.context = &f;
    f.platform.read8 = read8;
    f.platform.read16 = read16;
    f.platform.write8 = write8;
    f.platform.write16 = write16;
    f.platform.mask_irq = mask_irq;
    f.pcm.platform = &f.platform;
    f.cal = pcm_reference_scheduler_calibration;
    f.air = *f.cal.air;
    f.env = *f.cal.environment;
    f.cal.air = &f.air;
    f.cal.environment = &f.env;
    f.pcm.calibration = &f.cal;
    f.pcm.unresolved_task = PCM_TASK_COUNT;
}

static void seed(void)
{
    uint8_t *m = f.mem;
    f.pcm.scheduler.phase = m[2];
    f.pcm.scheduler.run_counter = word(m, 0xfd);
    f.pcm.runtime.monitor_freeze = (m[0x3b] & 4u) != 0;
    f.pcm.runtime.first_conversion = (m[0x43] & 128u) != 0;
    f.pcm.runtime.primary_faults = m[0x16];
    f.pcm.iac.input_fault = (m[0x17] & 128u) != 0;
    f.pcm.iac.startup_cancel = (m[0x3f] & 64u) != 0;
    f.pcm.transmission.adaptive_flags = m[0x11a];
    f.pcm.transmission.fault_flags_secondary = m[0x1d];
    f.pcm.spark.load_status = m[0x6f];
    f.pcm.spark.battery_sample = m[0xa7];
    f.pcm.io.raw_coolant = m[0x82d];
    f.pcm.io.auxiliary_reference = m[0xa5];
    f.pcm.io.barometric_sample = m[0x2f3];
    f.pcm.io.auxiliary_output = m[0x4e];
    f.pcm.io.coolant_conversion = m[0xa8];
    f.pcm.reference.coolant = m[6];
    f.pcm.iac.coolant_index = m[0x283];
    f.pcm.io.environmental_trim = m[0x1e5];
    f.pcm.io.environmental_factor = m[0x243];
    f.pcm.io.environmental_load = m[0x272];
    f.pcm.io.environmental_idle = m[0x1cb];
    f.pcm.io.environmental_density = m[0x1bb];
    f.pcm.knock.burst_gain = m[0x842];
    memcpy(f.air.coolant_table, m+0xfc45, sizeof(f.air.coolant_table));
    f.air.coolant_runtime_limit = word(m, 0x5b18);
    f.air.coolant_default_late = m[0x5b1a];
    f.air.coolant_default_early = m[0x5b1b];
    f.env.low_coolant_limit = m[0x48e3];
    f.env.low_coolant_subtract = m[0x48e8];
    memcpy(f.env.coolant_trim, m+0x4b64, sizeof(f.env.coolant_trim));
    memcpy(f.env.coolant_factor, m+0x4c8d, sizeof(f.env.coolant_factor));
    memcpy(f.env.coolant_load, m+0x4bad, sizeof(f.env.coolant_load));
    memcpy(f.env.coolant_idle, m+0x4b3c, sizeof(f.env.coolant_idle));
    f.env.density.limit = m[0x475f];
    f.env.density.values = m+0x4760;
    f.env.density.length = 17;
    f.cal.knock.burst_table_limit = m[0x46e3];
    memcpy(f.cal.knock.burst_curve, m+0x46e4, sizeof(f.cal.knock.burst_curve));
}

static void emit(PcmStatus s)
{
    uint8_t *m = f.mem;
    /* Check these backing writes independently from the named consumers. */
    printf("%u %u %u %u %u %u ", (unsigned)s, (unsigned)f.masked, (unsigned)m[0x16],
           (unsigned)m[0x1d], (unsigned)m[0x6f], (unsigned)f.pcm.knock.burst_gain);
    m[2] = f.pcm.scheduler.phase;
    m[0x3b] = (uint8_t)((m[0x3b] & ~4u) | (f.pcm.runtime.monitor_freeze ? 4u : 0));
    m[0x43] = (uint8_t)((m[0x43] & ~128u) | (f.pcm.runtime.first_conversion ? 128u : 0));
    m[0x16] = f.pcm.runtime.primary_faults;
    m[0x1d] = f.pcm.transmission.fault_flags_secondary;
    m[0x11a] = f.pcm.transmission.adaptive_flags;
    m[0x6f] = f.pcm.spark.load_status;
    m[0x4e] = f.pcm.io.auxiliary_output;
    m[0xa8] = f.pcm.io.coolant_conversion;
    m[6] = f.pcm.reference.coolant;
    m[0x283] = f.pcm.iac.coolant_index;
    m[0x1e5] = f.pcm.io.environmental_trim;
    m[0x243] = f.pcm.io.environmental_factor;
    m[0x272] = f.pcm.io.environmental_load;
    m[0x1cb] = f.pcm.io.environmental_idle;
    m[0x1bb] = f.pcm.io.environmental_density;
    for (unsigned a = 0; a < 0x350; a++) printf("%02x", (unsigned)m[a]);
    for (unsigned i = 0; i < f.used; i++) {
        Event e = f.events[i];
        printf(" %c%04x%04x", e.kind, (unsigned)e.address, (unsigned)e.value);
    }
    putchar('\n');
}

/* Stock restore bytes happen to equal the reset fill. Give each of the 51
 * restore locations a different value to make the order observable in RAM. */
static void check_adaptive_service(void)
{
    configure();
    seed();
    f.pcm.scheduler.phase = 0x14;
    f.pcm.runtime.monitor_freeze = true;
    f.pcm.serial.sessions = 2;
    f.pcm.serial.transmission_command = 4;
    f.mem[0x3a0] = 0xc0;
    uint8_t original_sum = 0, final_sum = 0;
    for (unsigned bank = 0; bank < 3; bank++) {
        unsigned dest = 0x2f8 + 17 * bank, source = 0x6a81 + 17 * bank;
        f.mem[0xbc65 + bank * 2] = (uint8_t)(dest >> 8);
        f.mem[0xbc66 + bank * 2] = (uint8_t)dest;
        f.mem[0xba32 + bank * 2] = (uint8_t)(source >> 8);
        f.mem[0xba33 + bank * 2] = (uint8_t)source;
        for (unsigned i = 0; i < 17; i++) {
            f.mem[dest+i] = (uint8_t)(dest + i);
            f.mem[source+i] = (uint8_t)(source + i + 13u);
            original_sum += f.mem[dest+i];
            final_sum += f.mem[source+i];
        }
    }
    f.mem[0x32b] = (uint8_t)(0u - original_sum);
    CHECK(pcm_service_transmission(&f.pcm) == PCM_OK && f.pcm.transmission.adaptive_flags == 0xc0);
    CHECK(pcm_dispatch_slot(&f.pcm) == PCM_OK && f.pcm.transmission.adaptive_flags == 0);
    CHECK(memcmp(f.mem+0x2f8, f.mem+0x6a81, 51) == 0 && f.mem[0x32b] == (uint8_t)(0u-final_sum));
    unsigned pairs = 0;
    for (unsigned i = 0; i < f.used; i++) {
        if (f.events[i].kind == 'm' && f.events[i].value == 1u) {
            CHECK(i+3 < f.used && f.events[i+1].kind == 'w' && f.events[i+2].address == 0x32b);
            CHECK(f.events[i+3].kind == 'm' && f.events[i+3].value == 0u);
            pairs++;
        }
    }
    CHECK(pairs == 102 && !f.masked);
    CHECK(pcm_boot_adaptive_validate(&f.pcm) == PCM_OK && memcmp(f.mem+0x2f8, f.mem+0x6a81, 51) == 0);
}

static void contracts(void)
{
    configure();
    seed();
    f.pcm.scheduler.phase = 4;
    f.pcm.runtime.monitor_freeze = true;
    f.pcm.runtime.primary_faults = 1;
    f.pcm.iac.input_fault = true;
    f.pcm.spark.load_status = f.mem[0x6f] = 0x09;
    CHECK(pcm_dispatch_slot(&f.pcm) == PCM_OK);
    CHECK(f.mem[0x6f] == 0x2d && f.pcm.spark.load_status == 0x2d);
    CHECK(f.pcm.unresolved_task == PCM_TASK_COUNT);
    f.mem[0x400f] = 1;
    f.mem[0x4f] = 0x80;
    CHECK(pcm_governor_target(&f.pcm) == PCM_OK && f.mem[0x299] == 255);
    CHECK(f.events[f.used-2].address == 0x6f && f.events[f.used-1].address == 0x299);
    configure();
    seed();
    f.pcm.scheduler.phase = 0x14;
    f.pcm.runtime.monitor_freeze = true;
    f.pcm.transmission.adaptive_flags = 0xc0;
    f.platform.mask_irq = NULL;
    CHECK(pcm_dispatch_slot(&f.pcm) == PCM_NO_HARDWARE);
    CHECK(f.pcm.transmission.adaptive_flags == 0x80 && f.mem[0x14b] == 0);
    check_adaptive_service();
    CHECK(pcm_slot_04(NULL) == PCM_BAD_CONFIGURATION);
    puts("Both scheduled groups, named fuel-fault publication and failed adaptive prefix passed.");
}

int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    if (strcmp(argv[1], "--contracts") == 0) { contracts(); return 0; }
    FILE *file = fopen(argv[1], "rb");
    CHECK(file && fread(image, 1, sizeof(image), file) == sizeof(image) && fclose(file) == 0);
    unsigned count, passes, fail, action, mask;
    while (scanf("%u %u %u %u %u", &passes, &fail, &action, &mask, &count) == 5) {
        configure();
        for (unsigned i = 0; i < count; i++) {
            unsigned a, b;
            CHECK(scanf("%u %u", &a, &b) == 2 && a <= 65535 && b < 256);
            f.mem[a] = (uint8_t)b;
        }
        seed();
        f.fail = fail;
        f.action = action;
        f.masked = mask != 0;
        PcmStatus status = PCM_OK;
        for (unsigned i = 0; i < passes && status == PCM_OK; i++) {
            if (i != 0) f.pcm.scheduler.phase = (uint8_t)((f.pcm.scheduler.phase + 16u) % 160u);
            status = pcm_dispatch_slot(&f.pcm);
        }
        emit(status);
    }
    return ferror(stdin) ? 2 : 0;
}
