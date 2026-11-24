#ifndef PSEUDO_SOURCE_HC11_BUS_H
#define PSEUDO_SOURCE_HC11_BUS_H
#include "pcm.h"

/* Resource classification models the source-programmed INIT/CS windows,
 * not an assertion that external memory or a particular ASIC is fitted. */
typedef enum {
    PCM_HC11_INTERNAL_RAM,
    PCM_HC11_EXTERNAL_GEN,
    PCM_HC11_CONDITIONAL_EEPROM,
    PCM_HC11_UNPROVEN_PROGRAM,
    PCM_HC11_CPU_REGISTERS,
    PCM_HC11_BOARD_IO1,
    PCM_HC11_BOARD_IO2,
    PCM_HC11_PROGRAM_IMAGE
} PcmHc11Resource;

enum {
    PCM_HC11_R8 = 1u, PCM_HC11_W8 = 2u,
    PCM_HC11_R16 = 4u, PCM_HC11_W16 = 8u
};

typedef struct {
    uint16_t first, last;  /* inclusive, non-overlapping, sorted */
    PcmHc11Resource resource;
    uint8_t permitted;     /* exact-width permissions, no implicit fallback */
} PcmHc11Window;

/* Raw operations have physical/target semantics. A word operation is ONE
 * logical request; it MUST preserve the documented high-byte/low-byte order,
 * register latches and any device side effects. It may take two bus cycles.
 * The backend never decomposes a word request into two read8/write8 calls.
 *
 * authorize_write is REQUIRED for ALL non-internal-RAM writes (even CPU
 * configuration, EEPROM and board output-off requests). This callback is
 * where a target must prove board-specific reset/authorization policy.
 * Returning failure must not publish any physical write. */
typedef struct {
    void *context;
    PcmStatus (*read8)(void *, uint16_t, uint8_t *);
    PcmStatus (*read16)(void *, uint16_t, uint16_t *);
    PcmStatus (*write8)(void *, uint16_t, uint8_t);
    PcmStatus (*write16)(void *, uint16_t, uint16_t);
    PcmStatus (*authorize_write)(void *, uint16_t, unsigned width, uint16_t value);
    PcmStatus (*mask_irq)(void *, bool);
    PcmStatus (*delay_cycles)(void *, uint16_t);
    PcmStatus (*check_stack)(void *, bool);
    PcmStatus (*capture_timer_stack_x)(void *, uint16_t *);
} PcmHc11Io;

typedef struct {
    PcmHc11Io io;
    const PcmHc11Window *windows; /* immutable ROM-resident target table */
    size_t count;
} PcmHc11Bus;

PcmHc11Resource pcm_hc11_classify(uint16_t address);
PcmStatus pcm_hc11_bus_bind(PcmHc11Bus *bus, PcmPlatform *platform,
                            const PcmHc11Io *io,
                            const PcmHc11Window *windows, size_t count);

/* Native primitive adapter. It only touches CPU addresses when compiled
 * with PCM_HC11_NATIVE_MMIO, which must be defined by a VERIFIED target
 * toolchain. Host calls return PCM_NO_HARDWARE instead of dereferencing
 * host process memory. Authorization remains mandatory in the mapped bus. */
void pcm_hc11_native_mmio_init(PcmHc11Io *io, void *context,
    PcmStatus (*authorize_write)(void *, uint16_t, unsigned, uint16_t));

#endif
