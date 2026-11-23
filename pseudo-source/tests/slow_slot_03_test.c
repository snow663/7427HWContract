/* Whole gear-slot fixture. RAM transactions stay visible through D4EB.
 * The C514 shadow and TCC state live in their regular named C owners. */
#include "control.h"
#include "scheduler.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(test) do { if (!(test)) { fprintf(stderr, "gear slot %d: %s\n", __LINE__, #test); exit(3); } } while (0)
typedef struct {
    char kind;
    uint16_t address, value;
} Event;
typedef struct {
    Pcm pcm;
    PcmPlatform platform;
    PcmCalibration calibration;
    PcmTransmissionCalibration transmission;
    uint8_t memory[65536];
    Event events[1536];
    unsigned count, fail_at, mutation, module;
} Fixture;

static Fixture fixture;
static uint8_t image[65536];

static uint16_t word(const uint8_t *bytes, uint16_t address)
{
    return (uint16_t)(((uint16_t)bytes[address] << 8) | bytes[(uint16_t)(address + 1u)]);
}

static PcmStatus record(Fixture *f, char kind, uint16_t address, uint16_t value)
{
    CHECK(f->count < sizeof(f->events) / sizeof(f->events[0]));
    f->events[f->count++] = (Event){kind, address, value};
    return f->count == f->fail_at ? PCM_NO_HARDWARE : PCM_OK;
}

static PcmStatus read8(void *context, uint16_t address, uint8_t *out)
{
    Fixture *f = context;
    uint8_t value = f->memory[address];
    PcmStatus status = record(f, 'r', address, value);
    if (status != PCM_OK) return status;
    *out = value;
    if (f->mutation == 1 && address == 0x5d30) {
        f->memory[0xd9] = 0;
        f->pcm.transmission.selected_gear = 0;
    }
    return PCM_OK;
}

static PcmStatus read16(void *context, uint16_t address, uint16_t *out)
{
    Fixture *f = context;
    uint16_t value = word(f->memory, address);
    PcmStatus status = record(f, 'R', address, value);
    if (status != PCM_OK) return status;
    *out = value;
    if (f->mutation == 2 && address == 0x5d6e) f->memory[address] ^= 0x3fu;
    return PCM_OK;
}

static PcmStatus write8(void *context, uint16_t address, uint8_t value)
{
    Fixture *f = context;
    PcmStatus status = record(f, 'w', address, value);
    if (status == PCM_OK) f->memory[address] = value;
    return status;
}

static PcmStatus write16(void *context, uint16_t address, uint16_t value)
{
    Fixture *f = context;
    PcmStatus status = record(f, 'W', address, value);
    if (status == PCM_OK) {
        f->memory[address] = (uint8_t)(value >> 8);
        f->memory[(uint16_t)(address + 1u)] = (uint8_t)value;
    }
    return status;
}

static PcmStatus module_call(void *context, uint16_t address)
{
    Fixture *f = context;
    CHECK(address == 0x1806);
    PcmStatus status = record(f, 'c', address, 0);
    if (status != PCM_OK || f->module == 2) return PCM_NO_HARDWARE;
    f->memory[0x103] = 4; /* Observable test module effect before F5D6. */
    f->pcm.transmission.service_gear = 4;
    return PCM_OK;
}

static void reset(Fixture *f)
{
    memset(f, 0, sizeof(*f));
    memcpy(f->memory, image, sizeof(image));
    f->platform.context = f;
    f->platform.read8 = read8;
    f->platform.read16 = read16;
    f->platform.write8 = write8;
    f->platform.write16 = write16;
    f->pcm.platform = &f->platform;
    f->pcm.calibration = &f->calibration;
    f->pcm.unresolved_task = PCM_TASK_COUNT;
    f->calibration.transmission = &f->transmission;
    f->transmission.gear_patterns = f->memory + 0xb319;
    f->transmission.gear_pattern_length = 256;
}

/* Seed named owners once, before dispatch. Subsequent gear and inhibit
 * publications come from the production controller, including on retained passes. */
static void seed(Fixture *f)
{
    PcmTransmission *t = &f->pcm.transmission;
    t->selected_gear = f->memory[0xd9];
    t->inhibit_flags = f->memory[0x99];
    t->fault_flags_primary = f->memory[0x1c];
    t->fault_flags_secondary = f->memory[0x1d];
    t->output_fault_flags = f->memory[0x8e];
    t->driver_inhibit = (f->memory[0x86] & 1u) != 0;
    t->output_shadow = f->memory[0x4c];
    t->service_gear = f->memory[0x103];
    t->current_service_enable = f->memory[0x39a];
    t->current_service_value = f->memory[0x39b];
    t->tcc_state = f->memory[0x8b];
    t->tcc_flags = f->memory[0x8a];
    t->tcc_command = word(f->memory, 0x126);
    t->tcc_lower_limit = word(f->memory, 0x12b);
    f->calibration.mode_f = f->memory[0x400f];
    f->platform.call_address = f->module ? module_call : NULL;
}

static PcmStatus dispatch(Pcm *pcm, uint8_t phase)
{
    pcm->scheduler.phase = phase;
    return pcm_dispatch_slot(pcm);
}

static PcmStatus execute(Fixture *f, unsigned entry, uint16_t x, uint16_t d, unsigned *result)
{
    Pcm *pcm = &f->pcm;
    uint16_t value = 0;
    bool valid = false;
    PcmStatus status;
    switch (entry) {
    case 3: case 11: return dispatch(pcm, (uint8_t)entry);
    case 0:
        status = dispatch(pcm, 3);
        if (status == PCM_OK) status = dispatch(pcm, 11);
        if (status == PCM_OK) status = dispatch(pcm, 3);
        return status;
    case 0xd8fe:
        status = pcm_transmission_descriptor(pcm, x, (uint8_t)(d >> 8), (uint8_t)d, &value, &valid);
        if (status == PCM_OK) *result = (unsigned)value | (valid ? 65536u : 0u);
        return status;
    case 0xd980: status = pcm_transmission_cold_offset(pcm, x, d, &value); break;
    case 0xd92e: status = pcm_transmission_temperature_gain(pcm, x, d, &value); break;
    case 0xd8a7: status = pcm_transmission_kickdown_rpm(pcm, x, (uint8_t)d, &value); break;
    default: return PCM_BAD_CONFIGURATION;
    }
    if (status == PCM_OK) *result = value;
    return status;
}

static void contracts(void)
{
    Fixture *f = &fixture;
    reset(f);
    f->memory[0x86] = 0x40; seed(f);
    CHECK(dispatch(&f->pcm, 3) == PCM_UNIMPLEMENTED);
    CHECK(f->pcm.unresolved_task == PCM_SLOT_03 && f->count == 1 && f->memory[0xf00] == 0);

    f->module = 2; seed(f);
    CHECK(dispatch(&f->pcm, 3) == PCM_NO_HARDWARE);
    CHECK(f->events[f->count - 1].kind == 'c' && f->memory[0xf00] == 0);

    reset(f); f->memory[0x86] = 0x40; f->module = 1;
    f->memory[0xb31c] = 3; seed(f);
    CHECK(dispatch(&f->pcm, 3) == PCM_OK);
    CHECK(f->events[1].kind == 'c' && f->events[2].address == 0xf00 && f->memory[0xf00] == 0xf7);
    CHECK(f->memory[0xd9] == 3 && f->pcm.transmission.selected_gear == 3);
    CHECK((f->pcm.transmission.output_shadow & 3u) == 3u && f->events[f->count - 1].address == 0x306a);

    reset(f); f->memory[0x86] = 0x40; f->memory[0x103] = 2;
    f->memory[0x99] = 8; seed(f);
    CHECK(dispatch(&f->pcm, 11) == PCM_OK && f->memory[0xf00] == 0);
    CHECK(f->pcm.transmission.inhibit_flags == 8 && f->pcm.transmission.selected_gear == 1);

    reset(f); f->fail_at = 2; seed(f);
    CHECK(dispatch(&f->pcm, 3) == PCM_NO_HARDWARE && f->count == 2 && f->memory[0xf00] == 0);
    CHECK(pcm_slot_03(NULL) == PCM_BAD_CONFIGURATION && pcm_slot_0b(NULL) == PCM_BAD_CONFIGURATION);
    puts("Both resident gear slots, optional module order, gear handoff and failure boundaries passed.");
}

static void emit(const Fixture *f, PcmStatus status, unsigned result)
{
    static const uint16_t observed[] = {
        0x83, 0x84, 0x85, 0x98, 0x99, 0xd9, 0x103, 0x135, 0x187, 0xf00, 0x306a, 0x306b
    };
    printf("%u %u %u", (unsigned)status, (unsigned)(f->pcm.unresolved_task == PCM_SLOT_03), result);
    for (unsigned i = 0; i < sizeof(observed) / sizeof(observed[0]); i++)
        printf(" %u", (unsigned)f->memory[observed[i]]);
    const PcmTransmission *t = &f->pcm.transmission;
    printf(" %u %u %u %u %u", (unsigned)t->selected_gear, (unsigned)t->inhibit_flags,
           (unsigned)t->service_gear, (unsigned)t->output_shadow, (unsigned)t->tcc_state);
    for (unsigned i = 0; i < f->count; i++) {
        const Event *e = &f->events[i];
        printf(" %c%04x%04x", e->kind, (unsigned)e->address, (unsigned)e->value);
    }
    putchar('\n');
}

int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    if (strcmp(argv[1], "--contracts") == 0) { contracts(); return 0; }
    FILE *file = fopen(argv[1], "rb");
    CHECK(file != NULL && fread(image, 1, sizeof(image), file) == sizeof(image));
    CHECK(fclose(file) == 0);
    unsigned entry, x, d, module, fail, mutation, alternate, count;
    while (scanf("%u %u %u %u %u %u %u %u", &entry, &x, &d, &module, &fail, &mutation, &alternate, &count) == 8) {
        Fixture *f = &fixture;
        reset(f);
        for (unsigned i = 0; i < count; i++) {
            unsigned address, value;
            CHECK(scanf("%u %u", &address, &value) == 2 && address <= 65535u && value <= 255u);
            f->memory[address] = (uint8_t)value;
        }
        f->module = module; f->fail_at = fail; f->mutation = mutation;
        f->platform.enable_resident_slow_slots = alternate != 0;
        seed(f);
        unsigned result = 0;
        PcmStatus status = execute(f, entry, (uint16_t)x, (uint16_t)d, &result);
        emit(f, status, result);
    }
    return ferror(stdin) ? 2 : 0;
}
