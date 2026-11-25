/* Intentionally failing readiness witness for the audited development base.
 * This links production C, not a replacement output-IRQ body.
 *
 * ROM evidence, factory_global_instructions.csv:
 * 7875 CE3000; 7878 8608; 787A A723: first write = byte[3023] <- 08.
 * 78D9 CE3000; 78DC 8610; 78DE A723: first write = byte[3023] <- 10.
 * This necessary acknowledgment does not depend on a later branch/calibration.
 * Native entry/RTI itself is supplied as a verified fixture precondition.
 * A future passing result proves only this necessary entry/acknowledgment
 * contract; it does not certify the rest of either output-control handler.
 */
#include "hc11_vector_contract.h"
#include <stdio.h>
#include <string.h>

typedef struct {
    uint8_t memory[65536];
    unsigned writes;
    uint16_t first_address;
    uint8_t first_value;
} Fixture;

static PcmStatus read_byte(void *context, uint16_t address, uint8_t *value)
{
    Fixture *fixture = context;
    *value = fixture->memory[address];
    return PCM_OK;
}

static PcmStatus write_byte(void *context, uint16_t address, uint8_t value)
{
    Fixture *fixture = context;
    if (fixture->writes++ == 0u) {
        fixture->first_address = address;
        fixture->first_value = value;
    }
    fixture->memory[address] = value;
    return PCM_OK;
}

static PcmStatus mask_irq(void *context, bool masked)
{
    (void)context;
    (void)masked;
    return PCM_OK;
}

int main(void)
{
    static Fixture fixture;
    const uint16_t vectors[] = {0xffe0u, 0xffe2u};
    const uint16_t handlers[] = {0x7875u, 0x78d9u};
    const uint8_t masks[] = {0x08u, 0x10u};
    unsigned failures = 0;
    for (unsigned index = 0; index < 2u; ++index) {
        memset(&fixture, 0, sizeof(fixture));
        Pcm pcm = {0};
        PcmCalibration calibration = {0};
        PcmPlatform platform = {0};
        platform.context = &fixture;
        platform.read8 = read_byte;
        platform.write8 = write_byte;
        platform.mask_irq = mask_irq;
        pcm.platform = &platform;
        pcm.calibration = &calibration;
        const PcmHc11NativeFrame frame = {
            .frame_verified = true, .entry_interrupts_masked = true
        };
        PcmHc11NativeAction action = PCM_HC11_NO_NATIVE_RETURN;
        PcmStatus status = pcm_hc11_vector_dispatch(&pcm, vectors[index], &frame, &action);
        if (fixture.writes == 0u || fixture.first_address != 0x3023u ||
            fixture.first_value != masks[index]) {
            fprintf(stderr,
                "FAIL vector %04X -> factory %04X: expected first write 3023=%02X; "
                "got status=%d action=%d writes=%u first=%04X:%02X\n",
                vectors[index], handlers[index], masks[index], status, action,
                fixture.writes, fixture.first_address, fixture.first_value);
            ++failures;
        }
    }
    if (failures) return 1;
    puts("Output IRQ necessary entry/acknowledgment contract passed; full handler equivalence remains separate.");
    return 0;
}
