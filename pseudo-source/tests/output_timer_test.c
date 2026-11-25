/* Host contracts and a baseline-compatible C/ROM comparison driver.
 *
 * Only the existing vector API is called for the new handlers, so this same
 * test source links against the preimplementation branch and fails there.
 * The provider accepts hardware addresses only: named RAM must remain in Pcm.
 * It models logical word transactions and timer W1C, not physical bus timing.
 *
 * Default stdin schema, decimal integers, one case per line:
 * count fail_at port mask flags ctl timer_seed timer_step toc4 toc5
 * pulse reservoir async compare_a compare_b extended_a extended_b [vectors...]
 * count is 1..8. State, total operation attempts and TCNT-read ordinal remain
 * live across vectors. Per-step event lists restart; a failed step ends a case.
 */
#include "hardware.h"
#include "hc11_vector_contract.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(value) do { if (!(value)) { \
    fprintf(stderr, "output_timer_test:%d: %s\n", __LINE__, #value); exit(1); \
} } while (0)

typedef struct { char kind; unsigned width; uint16_t address, value; } Event;
typedef struct {
    uint8_t registers[0x60];
    Event events[32];
    unsigned used, attempts, fail_at, timer_reads, unexpected_ram, mask_calls;
    uint16_t timer_seed, timer_step;
    PcmPlatform platform;
} Fixture;

static bool hardware(uint16_t address)
{
    return address >= 0x3000u && address < 0x3060u;
}

static uint16_t word(const Fixture *f, uint16_t address)
{
    CHECK(hardware(address) && hardware((uint16_t)(address + 1u)));
    unsigned offset = (unsigned)address - 0x3000u;
    return (uint16_t)(((uint16_t)f->registers[offset] << 8) |
                      f->registers[offset + 1u]);
}

static void put_word(Fixture *f, uint16_t address, uint16_t value)
{
    CHECK(hardware(address) && hardware((uint16_t)(address + 1u)));
    unsigned offset = (unsigned)address - 0x3000u;
    f->registers[offset] = (uint8_t)(value >> 8);
    f->registers[offset + 1u] = (uint8_t)value;
}

static PcmStatus record(Fixture *f, char kind, unsigned width,
                        uint16_t address, uint16_t value)
{
    if (++f->attempts == f->fail_at) return PCM_NO_HARDWARE;
    CHECK(f->used < sizeof(f->events) / sizeof(f->events[0]));
    f->events[f->used++] = (Event){kind, width, address, value};
    return PCM_OK;
}

static PcmStatus read_byte(void *context, uint16_t address, uint8_t *value)
{
    Fixture *f = context;
    if (!hardware(address)) { ++f->unexpected_ram; return PCM_NO_HARDWARE; }
    if (value == NULL) return PCM_BAD_CONFIGURATION;
    uint8_t sample = f->registers[address - 0x3000u];
    PcmStatus status = record(f, 'R', 8, address, sample);
    if (status == PCM_OK) *value = sample;
    return status;
}

static PcmStatus read_word(void *context, uint16_t address, uint16_t *value)
{
    Fixture *f = context;
    if (!hardware(address) || !hardware((uint16_t)(address + 1u))) {
        ++f->unexpected_ram; return PCM_NO_HARDWARE;
    }
    if (value == NULL) return PCM_BAD_CONFIGURATION;
    uint16_t sample = address == PCM_TCNT ?
        (uint16_t)(f->timer_seed + (uint32_t)f->timer_reads * f->timer_step) :
        word(f, address);
    PcmStatus status = record(f, 'R', 16, address, sample);
    if (status == PCM_OK) {
        *value = sample;
        if (address == PCM_TCNT) ++f->timer_reads;
    }
    return status;
}

static PcmStatus write_byte(void *context, uint16_t address, uint8_t value)
{
    Fixture *f = context;
    if (!hardware(address)) { ++f->unexpected_ram; return PCM_NO_HARDWARE; }
    PcmStatus status = record(f, 'W', 8, address, value);
    if (status == PCM_OK) {
        if (address == PCM_TFLG1) f->registers[address - 0x3000u] &= (uint8_t)~value;
        else f->registers[address - 0x3000u] = value;
    }
    return status;
}

static PcmStatus write_word(void *context, uint16_t address, uint16_t value)
{
    Fixture *f = context;
    if (!hardware(address) || !hardware((uint16_t)(address + 1u))) {
        ++f->unexpected_ram; return PCM_NO_HARDWARE;
    }
    PcmStatus status = record(f, 'W', 16, address, value);
    if (status == PCM_OK) put_word(f, address, value);
    return status;
}

static PcmStatus mask_irq(void *context, bool masked)
{
    Fixture *f = context;
    (void)masked;
    ++f->mask_calls;
    return PCM_BAD_CONFIGURATION; /* Neither leaf may change IRQ admission. */
}

static void initialize(Fixture *f, Pcm *pcm)
{
    memset(f, 0, sizeof(*f));
    memset(pcm, 0, sizeof(*pcm));
    f->platform.context = f;
    f->platform.read8 = read_byte;
    f->platform.read16 = read_word;
    f->platform.write8 = write_byte;
    f->platform.write16 = write_word;
    f->platform.mask_irq = mask_irq;
    pcm->platform = &f->platform;
    /* Deliberately no calibration object: these factory leaves read none. */
    pcm->scheduler.phase = 0x93;
    pcm->scheduler.pending = true;
    pcm->runtime.factory_mode = true;
    pcm->runtime.fuel_running = true;
    pcm->reference.pending = true;
    pcm->reference.timer_pulse = 1;
    pcm->reference.compare_a = 0x1006;
    pcm->reference.compare_b = 0x2006;
    pcm->reference.extended_a = 0xa15a;
    pcm->reference.extended_b = 0xb26b;
    pcm->fuel.acceleration_reservoir = 2;
    pcm->fuel.async_suppressed = true;
    /* Other canonical owners of factory byte0046 must survive its bit clear. */
    pcm->fuel.closed_seen = true;
    pcm->fuel.blm_invalid = true;
    pcm->fuel.cut_active = true;
    pcm->runtime.deceleration_fuel_cut = true;
    pcm->fuel.oxygen_error_positive = true;
    pcm->unresolved_task = PCM_TASK_COUNT;
    f->timer_seed = 0x1000;
    f->registers[PCM_TMSK1 - 0x3000u] = 0xff;
    f->registers[PCM_TFLG1 - 0x3000u] = 0xff;
    f->registers[PCM_TCTL1 - 0x3000u] = 0xff;
    put_word(f, PCM_TOC4, 0x2000);
    put_word(f, PCM_TOC5, 0x1000);
}

static uint16_t vector_for(bool bank_b) { return bank_b ? 0xffe2u : 0xffe0u; }
static uint16_t compare_for(bool bank_b) { return bank_b ? PCM_TOC4 : PCM_TOC5; }
static uint8_t mask_for(bool bank_b) { return bank_b ? 0x10u : 0x08u; }
static uint8_t action_for(bool bank_b) { return bank_b ? 0x04u : 0x01u; }

static PcmStatus invoke(Pcm *pcm, uint16_t vector, PcmHc11NativeAction *action)
{
    const PcmHc11NativeFrame frame = {
        .frame_verified = true, .entry_interrupts_masked = true
    };
    return pcm_hc11_vector_dispatch(pcm, vector, &frame, action);
}

static void unchanged_except_handler_owners(const Pcm *pcm, const Pcm *before,
                                           bool bank_b)
{
    Pcm normalized;
    memcpy(&normalized, pcm, sizeof(normalized));
    if (bank_b) normalized.reference.extended_b = before->reference.extended_b;
    else normalized.reference.extended_a = before->reference.extended_a;
    normalized.fuel.acceleration_reservoir = before->fuel.acceleration_reservoir;
    normalized.fuel.async_suppressed = before->fuel.async_suppressed;
    CHECK(memcmp(&normalized, before, sizeof(normalized)) == 0);
}

static void check_event(const Event *actual, const Event *expected)
{
    CHECK(actual->kind == expected->kind && actual->width == expected->width &&
          actual->address == expected->address && actual->value == expected->value);
}

/* Literal witnesses from the two resident instruction streams. route0 is
 * PORTA clear, route1 set/base-only, route2 set/shared-reservoir consumption. */
static unsigned prepare_route(Fixture *f, Pcm *pcm, bool bank_b,
                              unsigned route, Event expected[9])
{
    initialize(f, pcm);
    uint8_t mask = mask_for(bank_b), action = action_for(bank_b);
    uint16_t compare = compare_for(bank_b);
    put_word(f, compare, 0x1000);
    if (bank_b) pcm->reference.compare_b = 0x1006;
    f->registers[PCM_PORTA - 0x3000u] = route == 0 ? 0 : mask;
    pcm->fuel.async_suppressed = route != 1;
    unsigned n = 0;
    expected[n++] = (Event){'W', 8, PCM_TFLG1, mask};
    expected[n++] = (Event){'R', 8, PCM_PORTA, route == 0 ? 0 : mask};
    if (route != 0) {
        expected[n++] = (Event){'R', 8, PCM_TMSK1, 0xff};
        expected[n++] = (Event){'W', 8, PCM_TMSK1, (uint8_t)(0xffu & (uint8_t)~mask)};
    } else f->registers[PCM_TCTL1 - 0x3000u] = 0xa0;
    expected[n++] = (Event){'R', 8, PCM_TCTL1, route == 0 ? 0xa0 : 0xff};
    expected[n++] = (Event){'W', 8, PCM_TCTL1, route == 0 ?
                           (uint8_t)(0xa0u | action) : (uint8_t)(0xffu & (uint8_t)~action)};
    if (route != 0) expected[n++] = (Event){'R', 16, compare, 0x1000};
    expected[n++] = (Event){'R', 16, PCM_TCNT, 0x1000};
    expected[n++] = (Event){'W', 16, compare, route == 1 ? 0x1002 : 0x1006};
    return n;
}

static void test_routes_and_failures(void)
{
    for (unsigned bank = 0; bank < 2; ++bank) for (unsigned route = 0; route < 3; ++route) {
        Fixture f; Pcm pcm, before; Event expected[9];
        unsigned count = prepare_route(&f, &pcm, bank != 0, route, expected);
        memcpy(&before, &pcm, sizeof(before));
        PcmHc11NativeAction action = PCM_HC11_NO_NATIVE_RETURN;
        CHECK(invoke(&pcm, vector_for(bank != 0), &action) == PCM_OK);
        CHECK(action == PCM_HC11_NATIVE_RTI_REQUIRED && f.used == count);
        for (unsigned i = 0; i < count; ++i) check_event(&f.events[i], &expected[i]);
        CHECK(f.registers[PCM_TFLG1 - 0x3000u] == (uint8_t)(0xffu & (uint8_t)~mask_for(bank != 0)));
        CHECK(f.timer_reads == 1 && f.unexpected_ram == 0 && f.mask_calls == 0);
        uint16_t extended = bank ? pcm.reference.extended_b : pcm.reference.extended_a;
        CHECK(extended == (route == 0 ? (bank ? 0xb26b : 0xa15a) :
                           route == 1 ? 0x1002 : 0x1006));
        CHECK(pcm.fuel.acceleration_reservoir == (route == 2 ? 0 : 2));
        CHECK(pcm.fuel.async_suppressed == (route == 0));
        unchanged_except_handler_owners(&pcm, &before, bank != 0);

        for (unsigned failure = 1; failure <= count; ++failure) {
            prepare_route(&f, &pcm, bank != 0, route, expected);
            memcpy(&before, &pcm, sizeof(before));
            f.fail_at = failure;
            action = PCM_HC11_NATIVE_RTI_REQUIRED;
            CHECK(invoke(&pcm, vector_for(bank != 0), &action) == PCM_NO_HARDWARE);
            CHECK(action == PCM_HC11_NO_NATIVE_RETURN && f.attempts == failure);
            CHECK(f.used == failure - 1u && f.unexpected_ram == 0 && f.mask_calls == 0);
            for (unsigned i = 0; i < f.used; ++i) check_event(&f.events[i], &expected[i]);
            /* TCNT and final-write failures occur after the successful old-TOC
             * read, EXT store, and (when requested) shared state consumption. */
            bool published = route != 0 && failure >= 8u;
            extended = bank ? pcm.reference.extended_b : pcm.reference.extended_a;
            CHECK(extended == (published ? (route == 1 ? 0x1002 : 0x1006) :
                               (bank ? 0xb26b : 0xa15a)));
            CHECK(pcm.fuel.acceleration_reservoir == (published && route == 2 ? 0 : 2));
            CHECK(pcm.fuel.async_suppressed == (route != 1 && !(published && route == 2)));
            CHECK(word(&f, compare_for(bank != 0)) == 0x1000);
            unchanged_except_handler_owners(&pcm, &before, bank != 0);
        }
    }
}

static void test_entry_and_callbacks(void)
{
    for (unsigned bank = 0; bank < 2; ++bank) {
        Fixture f; Pcm pcm, before; Event expected[9];
        prepare_route(&f, &pcm, bank != 0, 2, expected);
        memcpy(&before, &pcm, sizeof(before));
        PcmHc11NativeFrame frame = {0};
        PcmHc11NativeAction action = PCM_HC11_NATIVE_RTI_REQUIRED;
        CHECK(pcm_hc11_vector_dispatch(&pcm, vector_for(bank != 0), &frame, &action) == PCM_STACK_BOUNDARY);
        CHECK(action == PCM_HC11_NO_NATIVE_RETURN && f.attempts == 0);
        frame.frame_verified = true;
        CHECK(pcm_hc11_vector_dispatch(&pcm, vector_for(bank != 0), &frame, &action) == PCM_STACK_BOUNDARY);
        CHECK(f.attempts == 0 && memcmp(&pcm, &before, sizeof(pcm)) == 0);
        pcm.platform = NULL;
        CHECK(invoke(&pcm, vector_for(bank != 0), &action) == PCM_NO_HARDWARE);
        CHECK(action == PCM_HC11_NO_NATIVE_RETURN && f.attempts == 0);

        for (unsigned missing = 0; missing < 4; ++missing) {
            prepare_route(&f, &pcm, bank != 0, 2, expected);
            if (missing == 0) f.platform.write8 = NULL;
            if (missing == 1) f.platform.read8 = NULL;
            if (missing == 2) f.platform.read16 = NULL;
            if (missing == 3) f.platform.write16 = NULL;
            CHECK(invoke(&pcm, vector_for(bank != 0), &action) == PCM_NO_HARDWARE);
            CHECK(action == PCM_HC11_NO_NATIVE_RETURN);
            CHECK(f.used == (missing == 0 ? 0u : missing == 1 ? 1u : missing == 2 ? 6u : 8u));
            CHECK(pcm.fuel.acceleration_reservoir == (missing == 3 ? 0 : 2));
            CHECK(pcm.fuel.async_suppressed == (missing != 3));
        }
    }
}

static void test_producer_sequences(void)
{
    for (unsigned bank = 0; bank < 2; ++bank) {
        Fixture f; Pcm pcm, before;
        initialize(&f, &pcm);
        f.timer_seed = 0xfffc;
        f.registers[PCM_PORTA - 0x3000u] = 0;
        pcm.reference.timer_delay = 6;
        CHECK(pcm_reference_timer_arm(&pcm, bank != 0) == PCM_OK);
        CHECK((bank ? pcm.reference.compare_b : pcm.reference.compare_a) == 2);
        CHECK(word(&f, compare_for(bank != 0)) == 2);
        /* Same live Pcm, no state serialization or raw RAM reload. The
         * provider rejects RAM accesses, including unsynchronized0821..28. */
        memcpy(&before, &pcm, sizeof(before));
        f.used = f.attempts = f.timer_reads = 0;
        f.timer_seed = 0xfffb;
        PcmHc11NativeAction action;
        CHECK(invoke(&pcm, vector_for(bank != 0), &action) == PCM_OK);
        CHECK(action == PCM_HC11_NATIVE_RTI_REQUIRED);
        CHECK(word(&f, compare_for(bank != 0)) == 2);
        CHECK(pcm.fuel.acceleration_reservoir == 2 && pcm.fuel.async_suppressed);
        CHECK(f.unexpected_ram == 0 && f.mask_calls == 0);
        unchanged_except_handler_owners(&pcm, &before, bank != 0);

        /* The crank producer publishes a new compare on the same state.
         * Supply the subsequent PORTA phase explicitly as a device input. */
        initialize(&f, &pcm);
        PcmCalibration cal = {0};
        cal.reference.crank_timer_gain = 128;
        pcm.calibration = &cal;
        pcm.reference.timer_pulse = 5;
        pcm.reference.crank_timer_latch = true;
        pcm.reference.event_age = 1;
        f.registers[PCM_TFLG1 - 0x3000u] = (uint8_t)bank;
        CHECK(pcm_reference_crank_timer(&pcm) == PCM_OK);
        CHECK(pcm.reference.timer_pulse == (bank ? 5 : 6));
        CHECK(word(&f, compare_for(bank != 0)) == (bank ? 0x100a : 0x100c));
        f.registers[PCM_PORTA - 0x3000u] = mask_for(bank != 0);
        f.used = f.attempts = 0;
        memcpy(&before, &pcm, sizeof(before));
        CHECK(invoke(&pcm, vector_for(bank != 0), &action) == PCM_OK);
        CHECK(word(&f, compare_for(bank != 0)) == (bank ? 0x1018 : 0x101c));
        CHECK(pcm.fuel.acceleration_reservoir == 0 && !pcm.fuel.async_suppressed);
        CHECK(f.unexpected_ram == 0 && f.mask_calls == 0);
        unchanged_except_handler_owners(&pcm, &before, bank != 0);
    }
}

static void test_retained_consumption(void)
{
    for (unsigned first_bank = 0; first_bank < 2; ++first_bank) {
        Fixture f; Pcm pcm;
        initialize(&f, &pcm);
        f.registers[PCM_PORTA - 0x3000u] = 0x18;
        PcmHc11NativeAction action;
        CHECK(invoke(&pcm, vector_for(first_bank != 0), &action) == PCM_OK);
        CHECK(word(&f, compare_for(first_bank != 0)) == (first_bank ? 0x2006 : 0x1006));
        CHECK(pcm.fuel.acceleration_reservoir == 0 && !pcm.fuel.async_suppressed);
        f.used = 0;
        CHECK(invoke(&pcm, vector_for(first_bank == 0), &action) == PCM_OK);
        CHECK(pcm.reference.extended_a == (first_bank ? 0x1002 : 0x1006));
        CHECK(pcm.reference.extended_b == (first_bank ? 0x2006 : 0x2002));

        initialize(&f, &pcm);
        if (first_bank) pcm.reference.compare_b = 0x1006;
        CHECK(invoke(&pcm, vector_for(first_bank != 0), &action) == PCM_OK);
        CHECK(pcm.fuel.acceleration_reservoir == 2 && pcm.fuel.async_suppressed);
        f.registers[PCM_PORTA - 0x3000u] = mask_for(first_bank != 0);
        f.used = 0;
        CHECK(invoke(&pcm, vector_for(first_bank != 0), &action) == PCM_OK);
        CHECK(word(&f, compare_for(first_bank != 0)) == 0x100c);
        CHECK(pcm.fuel.acceleration_reservoir == 0 && !pcm.fuel.async_suppressed);
    }
}

static void print_step(const Fixture *f, const Pcm *pcm, PcmStatus status,
                       PcmHc11NativeAction action)
{
    printf("{\"status\":%u,\"action\":%u,\"state\":[%u,%u,%u,%u,%u,%u,%u],"
           "\"io\":[%u,%u,%u,%u,%u,%u],\"events\":[",
           (unsigned)status, (unsigned)action,
           (unsigned)pcm->reference.timer_pulse, (unsigned)pcm->fuel.acceleration_reservoir,
           (unsigned)pcm->fuel.async_suppressed, (unsigned)pcm->reference.compare_a,
           (unsigned)pcm->reference.compare_b, (unsigned)pcm->reference.extended_a,
           (unsigned)pcm->reference.extended_b,
           f->registers[PCM_PORTA - 0x3000u], f->registers[PCM_TMSK1 - 0x3000u],
           f->registers[PCM_TFLG1 - 0x3000u], f->registers[PCM_TCTL1 - 0x3000u],
           (unsigned)word(f, PCM_TOC4), (unsigned)word(f, PCM_TOC5));
    for (unsigned i = 0; i < f->used; ++i) {
        const Event *e = &f->events[i];
        printf("%s[\"%c\",%u,%u,%u]", i ? "," : "", e->kind, e->width,
               (unsigned)e->address, (unsigned)e->value);
    }
    printf("]}");
}

static int batch_cases(void)
{
    for (;;) {
        unsigned input[17], vectors[8];
        int first = scanf("%u", &input[0]);
        if (first == EOF) return 0;
        if (first != 1) return 2;
        for (unsigned i = 1; i < 17; ++i) if (scanf("%u", &input[i]) != 1) return 2;
        if (input[0] < 1 || input[0] > 8 || input[1] > 1024 || input[12] > 1) return 2;
        for (unsigned i = 2; i < 17; ++i) if (input[i] > (i < 6 ? 255u : 65535u)) return 2;
        for (unsigned i = 0; i < input[0]; ++i) {
            if (scanf("%u", &vectors[i]) != 1 || (vectors[i] != 0xffe0u && vectors[i] != 0xffe2u)) return 2;
        }
        Fixture f; Pcm pcm;
        initialize(&f, &pcm);
        f.fail_at = input[1];
        f.registers[PCM_PORTA - 0x3000u] = (uint8_t)input[2];
        f.registers[PCM_TMSK1 - 0x3000u] = (uint8_t)input[3];
        f.registers[PCM_TFLG1 - 0x3000u] = (uint8_t)input[4];
        f.registers[PCM_TCTL1 - 0x3000u] = (uint8_t)input[5];
        f.timer_seed = (uint16_t)input[6]; f.timer_step = (uint16_t)input[7];
        put_word(&f, PCM_TOC4, (uint16_t)input[8]); put_word(&f, PCM_TOC5, (uint16_t)input[9]);
        pcm.reference.timer_pulse = (uint16_t)input[10];
        pcm.fuel.acceleration_reservoir = (uint16_t)input[11];
        pcm.fuel.async_suppressed = input[12] != 0;
        pcm.reference.compare_a = (uint16_t)input[13]; pcm.reference.compare_b = (uint16_t)input[14];
        pcm.reference.extended_a = (uint16_t)input[15]; pcm.reference.extended_b = (uint16_t)input[16];
        printf("{\"steps\":[");
        for (unsigned step = 0; step < input[0]; ++step) {
            f.used = 0;
            Pcm before; memcpy(&before, &pcm, sizeof(before));
            PcmHc11NativeAction action = PCM_HC11_NATIVE_RTI_REQUIRED;
            PcmStatus status = invoke(&pcm, (uint16_t)vectors[step], &action);
            CHECK(f.unexpected_ram == 0 && f.mask_calls == 0);
            unchanged_except_handler_owners(&pcm, &before, vectors[step] == 0xffe2u);
            if (step != 0) putchar(',');
            print_step(&f, &pcm, status, action);
            if (status != PCM_OK) break;
        }
        puts("]}");
    }
}

int main(int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "--contracts") == 0) {
        test_routes_and_failures();
        test_entry_and_callbacks();
        test_producer_sequences();
        test_retained_consumption();
        puts("Output timer contracts: both vectors, ordered I/O, all route failure prefixes, "
             "entry guards, same-Pcm REF producers and retained consumption passed.");
        return 0;
    }
    if (argc != 1) return 2;
    return batch_cases();
}
