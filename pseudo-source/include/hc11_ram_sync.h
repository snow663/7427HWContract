#ifndef PCM_HC11_RAM_SYNC_H
#define PCM_HC11_RAM_SYNC_H
#include "pcm.h"

/* Explicit, source-owned INTERNAL RAM publication.
 * Does NOT allocate a second memory mirror or infer external RAM backing.
 * Call only inside a target-verified critical section that excludes EVERY
 * writer of the named Pcm state, not merely the timer ISR. */
typedef struct {
    uint16_t address;  /* CPU address, ascending, no overlaps */
    uint8_t width;     /* 1 byte, or 2-byte big-endian logical word */
    uint16_t mask;     /* byte: subset of named owner bits; word: 0xFFFF */
} PcmRamSyncEntry;

typedef struct {
    void *context;
    /* Return PCM_OK only when hardware interrupts and competing producers
     * are excluded for the entire call; never disable/unmask IRQs here. */
    PcmStatus (*verify_exclusive)(void *);
} PcmRamSyncGuard;

typedef struct {
    size_t examined;        /* physical reads attempted, including failed */
    size_t written;         /* successful physical writes */
    size_t already_equal;   /* backing matches source-owned state */
    size_t failed_index;    /* == count on success or preflight rejection */
} PcmRamSyncReport;

/* Preconditions: bind_fuel_ram_owners, explicit verified critical guard,
 * real physical callback and source-owned address/mask grants. Validate
 * the WHOLE entry list before the first bus access. Reads/writes use raw
 * PcmPlatform callbacks, NOT pcm_read8/pcm_read16 (which overlay C state). */ 
PcmStatus pcm_ram_sync_publish(Pcm *pcm, const PcmRamSyncEntry *entries,
                               size_t count, const PcmRamSyncGuard *guard,
                               PcmRamSyncReport *report);
#endif
