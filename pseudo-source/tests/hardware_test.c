#include "startup.h"
#include "calibration.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(x) do { if (!(x)) { fprintf(stderr, "Check failed at %s:%d: %s\n", __FILE__, __LINE__, #x); exit(1); } } while (0)

typedef struct { char kind; unsigned width; uint16_t address, value; } Event;
typedef struct {
    uint8_t memory[65536]; /* Host peripheral fixture only. */
    Event events[128];
    unsigned used, attempts, fail_at, strobe_reads, strobe_writes;
    uint16_t board_readback;
    uint8_t strobe_samples[2];
    bool mutate_rpm, inhibit_after_strobe;
    Pcm *pcm;
    PcmPlatform platform;
} Fixture;

static PcmStatus record(Fixture *f, char kind, unsigned width, uint16_t address, uint16_t value)
{
    if (++f->attempts == f->fail_at) return PCM_NO_HARDWARE;
    CHECK(f->used < sizeof(f->events) / sizeof(f->events[0]));
    f->events[f->used++] = (Event){kind, width, address, value};
    return PCM_OK;
}
static PcmStatus read8(void *context, uint16_t address, uint8_t *value)
{
    Fixture *f = context;
    uint8_t sample = f->memory[address];
    if (address == PCM_REFERENCE_STROBE) {
        CHECK(f->strobe_reads < 2);
        sample = f->strobe_samples[f->strobe_reads++];
    }
    PcmStatus result = record(f, 'R', 8, address, sample);
    if (result == PCM_OK) *value = sample;
    return result;
}
static PcmStatus read16(void *context, uint16_t address, uint16_t *value)
{
    Fixture *f = context;
    uint16_t sample = (uint16_t)((uint16_t)f->memory[address] * 256u + f->memory[(uint16_t)(address + 1u)]);
    if (address == PCM_BOARD_CONTROL) sample = f->board_readback;
    PcmStatus result = record(f, 'R', 16, address, sample);
    if (result == PCM_OK) {
        *value = sample;
        if (address == PCM_TCNT && f->mutate_rpm) f->pcm->reference.rpm_coordinate = 255;
    }
    return result;
}
static PcmStatus write8(void *context, uint16_t address, uint8_t value)
{
    Fixture *f = context;
    PcmStatus result = record(f, 'W', 8, address, value);
    if (result == PCM_OK) {
        f->memory[address] = value;
        if (address == PCM_REFERENCE_STROBE && ++f->strobe_writes == 2 && f->inhibit_after_strobe)
            f->pcm->reference.latch_inhibited = true;
    }
    return result;
}
static PcmStatus write16(void *context, uint16_t address, uint16_t value)
{
    Fixture *f = context;
    PcmStatus result = record(f, 'W', 16, address, value);
    if (result == PCM_OK) {
        f->memory[address] = (uint8_t)(value >> 8);
        f->memory[(uint16_t)(address + 1u)] = (uint8_t)value;
    }
    return result;
}
static PcmStatus mask_irq(void *context, bool masked)
{
    (void)context;
    CHECK(masked);
    return PCM_OK;
}
static PcmStatus entry_precondition(Pcm *pcm, PcmTask task)
{
    (void)pcm;
    CHECK(task == PCM_RESET_ENTRY);
    return PCM_OK;
}
static void init(Fixture *f, Pcm *pcm)
{
    memset(f, 0, sizeof(*f));
    memset(pcm, 0, sizeof(*pcm));
    f->pcm = pcm;
    f->platform.context = f;
    f->platform.read8 = read8;
    f->platform.read16 = read16;
    f->platform.write8 = write8;
    f->platform.write16 = write16;
    f->platform.mask_irq = mask_irq;
    pcm->platform = &f->platform;
    pcm->calibration = &pcm_reference_scheduler_calibration;
    pcm->unresolved_task = PCM_TASK_COUNT;
}
static void print_result(const Fixture *f, const Pcm *pcm, PcmStatus status)
{
    printf("{\"status\":%u,\"pending\":%u,\"tail\":%u,\"events\":[", (unsigned)status,
           (unsigned)pcm->reference.pending, 0u);
    for (unsigned index = 0; index < f->used; ++index) {
        const Event *event = &f->events[index];
        printf("%s[\"%c\",%u,%u,%u]", index ? "," : "", event->kind, event->width,
               (unsigned)event->address, (unsigned)event->value);
    }
    puts("]}");
}
static void test_failure_prefixes(void)
{
    static Fixture f;
    Pcm pcm;
    const PcmRoutine routines[] = {pcm_reset_cpu, pcm_reset_outputs, pcm_reference_prefix};
    unsigned checks = 0;
    for (unsigned routine = 0; routine < sizeof(routines) / sizeof(routines[0]); ++routine) {
        init(&f, &pcm);
        PcmStatus status = routines[routine](&pcm);
        CHECK(status == (PCM_OK));
        unsigned operations = f.attempts;
        CHECK(operations > 0);
        for (unsigned failure = 1; failure <= operations; ++failure) {
            init(&f, &pcm);
            f.fail_at = failure;
            CHECK(routines[routine](&pcm) == PCM_NO_HARDWARE);
            CHECK(f.attempts == failure && f.used == failure - 1);
            CHECK(pcm.unresolved_task == PCM_TASK_COUNT);
            if (routine == 2) CHECK(pcm.reference.pending == (failure == operations));
            ++checks;
        }
    }
    CHECK(checks == 64); /* 23 CPU, 34 output-init, 7 REF transactions. */
}
static void test_entry_and_continuation_boundaries(void)
{
    static Fixture f;
    Pcm pcm;
    init(&f, &pcm);
    CHECK(pcm_reset_sequence(&pcm, &f.platform, &pcm_reference_scheduler_calibration) == PCM_UNIMPLEMENTED);
    CHECK(pcm.unresolved_task == PCM_RESET_ENTRY && f.used == 0);
    init(&f, &pcm);
    f.platform.task[PCM_RESET_ENTRY] = entry_precondition;
    CHECK(pcm_reset_sequence(&pcm, &f.platform, &pcm_reference_scheduler_calibration) == PCM_UNIMPLEMENTED);
    CHECK(pcm.unresolved_task == PCM_RESET_RAM && f.used == 57);
    init(&f, &pcm);
    pcm.reference.pending = true;
    pcm.runtime.factory_mode = true;
    CHECK(pcm_reference_prefix(&pcm) == PCM_FACTORY_BOUNDARY && pcm.reference.pending && f.used == 0);
    init(&f, &pcm);
    pcm.runtime.ignition_off = true; /* RAM0051.3 is not the0044.4 latch gate. */
    pcm.scheduler.pending = true;
    CHECK(pcm_reference_prefix(&pcm) == PCM_OK);
    CHECK(pcm.reference.pending && pcm.scheduler.pending && pcm.unresolved_task == PCM_TASK_COUNT);
    init(&f, &pcm);
    pcm.calibration = NULL;
    CHECK(pcm_reset_outputs(&pcm) == PCM_BAD_CONFIGURATION && f.used == 0);
    CHECK(pcm_reference_prefix(&pcm) == PCM_BAD_CONFIGURATION && f.used == 0);
    init(&f, &pcm);
    f.platform.read16 = NULL;
    CHECK(pcm_reference_prefix(&pcm) == PCM_NO_HARDWARE && f.used == 0);
}
static void test_gate_sampling(void)
{
    static Fixture f;
    Pcm pcm;
    init(&f, &pcm);
    f.mutate_rpm = true;
    CHECK(pcm_reference_prefix(&pcm) == PCM_OK);
    CHECK(f.events[1].address == PCM_TOC1 && f.events[1].value == 0x00db);
    init(&f, &pcm);
    f.inhibit_after_strobe = true;
    CHECK(pcm_reference_prefix(&pcm) == PCM_OK && !pcm.reference.pending);
}
int main(int argc, char **argv)
{
    static Fixture f;
    Pcm pcm;
    if (argc == 2 && strcmp(argv[1], "--boot") == 0) {
        unsigned option, readback, serial;
        while (scanf("%u %u %u", &option, &readback, &serial) == 3) {
            if (option > 1 || readback > 65535 || serial > 65535) return 2;
            init(&f, &pcm);
            PcmCalibration calibration = pcm_reference_scheduler_calibration;
            if (option) calibration.board_startup_word = 0xb91a;
            pcm.calibration = &calibration;
            f.board_readback = (uint16_t)readback;
            f.memory[PCM_SCSR] = (uint8_t)(serial >> 8);
            f.memory[PCM_SCDR] = (uint8_t)serial;
            PcmStatus result = pcm_reset_cpu(&pcm);
            if (result == PCM_OK) result = pcm_reset_outputs(&pcm);
            print_result(&f, &pcm, result);
        }
        return 0;
    }
    if (argc == 2 && strcmp(argv[1], "--reference") == 0) {
        unsigned timer, rpm, pending, inhibited, factory, first, second;
        while (scanf("%u %u %u %u %u %u %u", &timer, &rpm, &pending, &inhibited, &factory, &first, &second) == 7) {
            if (timer > 65535 || rpm > 255 || pending > 1 || inhibited > 1 || factory > 1 || first > 255 || second > 255) return 2;
            init(&f, &pcm);
            f.memory[PCM_TCNT] = (uint8_t)(timer >> 8);
            f.memory[PCM_TCNT + 1] = (uint8_t)timer;
            f.strobe_samples[0] = (uint8_t)first;
            f.strobe_samples[1] = (uint8_t)second;
            pcm.reference.rpm_coordinate = (uint8_t)rpm;
            pcm.reference.pending = pending != 0;
            pcm.reference.latch_inhibited = inhibited != 0;
            pcm.runtime.factory_mode = factory != 0;
            PcmStatus result = pcm_reference_prefix(&pcm);
            print_result(&f, &pcm, result);
        }
        return 0;
    }
    test_failure_prefixes();
    test_entry_and_continuation_boundaries();
    test_gate_sampling();
    init(&f, &pcm);
    pcm.reference.sample_map = true;
    pcm.reference.map_sample = 0x42;
    CHECK(pcm_reference_irq(&pcm) == PCM_NO_HARDWARE);
    CHECK(f.used == 8 && f.events[7].address == PCM_ADCTL);
    CHECK(pcm.reference.map_sample == 0x42);

    puts("64 hardware failure prefixes, startup/REF boundaries and gate-sampling checks passed.");
    return 0;
}
