#ifndef MANUAL_IDLE_H
#define MANUAL_IDLE_H
#include <stdint.h>

/* Host reference for the HC11 strategy. Addresses describe the simulation
 * overlay only. This is not a compiled target ABI or an installed ROM patch.
 * The memory argument is the full 64K CPU address view, including calibration.
 * Functions return pre-BARO Q8.8 air. The resident converter/driver owns steps.
 */
void mi_init(uint8_t memory[65536]);
void mi_target(uint8_t memory[65536]);
uint16_t mi_stopped(uint8_t memory[65536]);
uint16_t mi_run(uint8_t memory[65536]);
#endif
