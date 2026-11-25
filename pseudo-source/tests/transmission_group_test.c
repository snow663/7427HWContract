#include "control.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint8_t image[65536], memory[65536];
static unsigned writes, fail_at, mutate, limit_reads;

static PcmStatus read_byte(void *context, uint16_t a, uint8_t *v)
{
    (void)context;
    *v = memory[a];
    if (mutate == 5 && a == 0xde) *v = 8;
    if (mutate == 3 && a == 0xd9) memory[a] = 0;
    if (mutate == 1 && a == 0x70d1 && ++limit_reads == 2) memory[a] = 0;
    if (mutate == 2 && a == 0x70cf) memory[a] = 0;
    return PCM_OK;
}

static PcmStatus read_word(void *context, uint16_t a, uint16_t *v)
{
    (void)context;
    *v = (uint16_t)((uint16_t)memory[a] << 8) | memory[(uint16_t)(a + 1u)];
    return PCM_OK;
}

static PcmStatus write_byte(void *context, uint16_t a, uint8_t v)
{
    (void)context;
    printf(" b%04x%02x", (unsigned)a, (unsigned)v);
    if (++writes == fail_at) return PCM_NO_HARDWARE;
    memory[a] = v;
    if (mutate == 4 && a == 0xe1) memory[0x93] = 0;
    return PCM_OK;
}

static PcmStatus write_word(void *context, uint16_t a, uint16_t v)
{
    (void)context;
    printf(" w%04x%04x", (unsigned)a, (unsigned)v);
    if (++writes == fail_at) return PCM_NO_HARDWARE;
    memory[a] = (uint8_t)(v >> 8);
    memory[(uint16_t)(a + 1u)] = (uint8_t)v;
    return PCM_OK;
}

static PcmStatus mask(void *context, bool masked)
{
    (void)context;
    printf(" %s", masked ? "sei" : "cli");
    return PCM_OK;
}

int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    FILE *file = fopen(argv[1], "rb");
    if (!file || fread(image, 1, sizeof(image), file) != sizeof(image)) return 2;
    fclose(file);
    PcmPlatform platform = {.read8=read_byte, .read16=read_word, .write8=write_byte, .write16=write_word, .mask_irq=mask};
    unsigned entry, passes, size;
    while (scanf("%x%u%u%u%u", &entry, &passes, &fail_at, &mutate, &size) == 5) {
        memcpy(memory, image, sizeof(memory));
        for (unsigned i=0; i<size; ++i) {
            unsigned a, v;
            if (scanf("%u%u", &a, &v) != 2 || a >= sizeof(memory) || v > 255) return 2;
            memory[a] = (uint8_t)v;
        }
        Pcm pcm = {.platform=&platform};
        pcm.runtime.monitor_freeze = (memory[0x3b] & 4u) != 0;
        pcm.spark.transmission_status = memory[0xa4];
        pcm.spark.transmission_retard = memory[0x15a];
        pcm.transmission.selected_gear = memory[0xd9];
        pcm.transmission.inhibit_flags = memory[0x99];
        pcm.spark.rpm_low_coordinate = memory[0x61];
        pcm.reference.rpm_coordinate = memory[0x62];
        pcm.spark.load_coordinate = memory[0x1c0];
        limit_reads = writes = 0;
        for (unsigned i=0; i<passes; ++i) {
            PcmStatus result;
            uint8_t correction = 0;
            uint16_t factor = 0;
            switch (entry) {
            case 0xc271: result = pcm_tcc_base_curve(&pcm, 0x6db3, 0x10b); break;
            case 0xb88d: result = pcm_pressure_modifiers(&pcm, memory[0x142], &correction); break;
            case 0xbe5c: result = pcm_pressure_current_reference(&pcm); break;
            case 0xbebc: result = pcm_tcc_throttle_events(&pcm); break;
            case 0xbf62: result = pcm_tcc_event_timers(&pcm); break;
            case 0xbc77: result = pcm_pressure_shift_reduction(&pcm, memory[0x142], &correction); break;
            case 0xd969: result = pcm_pressure_baro_factor(&pcm, 0x70e0, &factor); break;
            case 0xb91d: result = pcm_pressure_adaptive_cell(&pcm, &correction); break;
            case 0xba38: result = pcm_pressure_learning_count(&pcm); break;
            case 0xe664: result = pcm_transmission_fault_gate_664(&pcm); break;
            case 0xb32d: result = pcm_shift_control(&pcm); break;
            case 0xb367: result = pcm_shift_observation(&pcm); break;
            case 0xba65: result = pcm_shift_adaptive_learning(&pcm); break;
            case 0xb4b2: result = pcm_shift_learning_reasons(&pcm); break;
            case 0xf131: result = pcm_long_shift_diagnostic(&pcm); break;
            case 0xb334: result = pcm_transmission_movement(&pcm); break;
            case 0xe654: result = pcm_transmission_fault_gate_654(&pcm); break;
            case 0xc4e5: result = pcm_transmission_spark(&pcm); break;
            case 0xd9b7: result = pcm_transmission_spark_mode(&pcm); break;
            case 0xda6f: result = pcm_transmission_range_retard(&pcm); break;
            case 0xdae2: result = pcm_transmission_shift_retard(&pcm); break;
            default: return 2;
            }
            memory[0xa4] = pcm.spark.transmission_status;
            memory[0x15a] = pcm.spark.transmission_retard;
            if (result != PCM_OK && result != PCM_NO_HARDWARE) return 1;
            if (entry == 0xd969 && result == PCM_OK) printf(" d%04x", (unsigned)factor);
            if ((entry == 0xb91d || entry == 0xbc77 || entry == 0xb88d) && result == PCM_OK) printf(" a%02x", (unsigned)correction);
            printf(" %s ", result == PCM_OK ? "ok" : "failed");
            for (unsigned a=0; a<0x350; ++a) printf("%02x",(unsigned)memory[a]);
            if (result != PCM_OK) break;
        }
        putchar('\n');
    }
    return ferror(stdin) != 0;
}
