#include "manual_idle.h"
#include "manual_idle_layout.h"
#include <stdbool.h>

static uint16_t word(const uint8_t *m, unsigned a)
{ return (uint16_t)((uint16_t)m[a] * 256u + m[a + 1u]); }
static void put(uint8_t *m, unsigned a, uint16_t value)
{ m[a] = (uint8_t)(value >> 8); m[a + 1u] = (uint8_t)value; }
static uint16_t cap(uint32_t value)
{ return value > 65535u ? 65535u : (uint16_t)value; }
static uint16_t sub(uint16_t a, uint16_t b)
{ return a > b ? (uint16_t)(a - b) : 0; }

/* Resident F4C1 arithmetic: signed direction with rounded magnitude. */
static uint8_t curve(const uint8_t *m, unsigned table, uint8_t coordinate)
{
    unsigned k = coordinate >> 4, fraction = (coordinate & 15u) * 16u;
    int first = m[table + k], next = m[table + k + 1u];
    unsigned distance = (unsigned)(next > first ? next - first : first - next);
    unsigned delta = (distance * fraction + 128u) >> 8;
    return (uint8_t)(next >= first ? first + (int)delta : first - (int)delta);
}

/* F4B6's serialized descriptor is a scale byte followed by knots. Length is
 * a host contract, not another ROM byte. This preserved table has five knots. */
static uint8_t scaled(const uint8_t *m, unsigned table, uint8_t coordinate)
{
    uint16_t index = (uint16_t)coordinate * m[table];
    unsigned knot = index >> 8, fraction = index & 255u;
    int first = m[table + 1u + knot], next = m[table + 2u + knot];
    unsigned distance = (unsigned)(next > first ? next - first : first - next);
    unsigned delta = (distance * fraction + 128u) >> 8;
    return (uint8_t)(next >= first ? first + (int)delta : first - (int)delta);
}

void mi_init(uint8_t m[65536])
{
    uint16_t seed = (uint16_t)m[MI_CAL_SEED] * 256u;
    put(m, MI_INTEGRAL, seed); put(m, 0x0862, seed); m[0x086a] = m[MI_CAL_SEED];
    put(m, MI_FOLLOWER, 0); put(m, MI_P_WORD, 0);
    put(m, 0x087d, 65535); put(m, 0x0880, 0); put(m, 0x0889, 0);
    m[MI_QUALIFY] = m[0x087f] = m[0x085f] = m[0x086d] = 0;
    m[0x36] &= (uint8_t)~0x9fu; m[9] &= (uint8_t)~0x30u;
    m[0x18] &= (uint8_t)~8u;
    m[MI_START_AIR] = m[MI_CAL_START_AIR];
    m[MI_START_DIV] = m[MI_CAL_START_DIV];
    m[MI_SIGNATURE] = 0xa5;
}

void mi_target(uint8_t m[65536])
{
    if (!(m[0x38] & 0x40u)) {
        uint8_t target = curve(m, 0xff60, m[0x0283]);
        if (m[0x085f] != 0 && target < m[0x085f]) target = m[0x085f] - 1u;
        m[0x085f] = m[0x0857] = target;
    }
    m[0x0868] = m[0x0857] >= m[MI_CAL_STALL_ERROR]
        ? m[0x0857] - m[MI_CAL_STALL_ERROR] : 0;
    m[0x086a] = m[MI_INTEGRAL];
}

static void follow(uint8_t *m)
{
    uint8_t above_closed = m[0x01d9] > m[MI_CAL_TPS_EXIT]
        ? m[0x01d9] - m[MI_CAL_TPS_EXIT] : 0;
    uint8_t desired = above_closed < m[MI_CAL_FOLLOWER_CAP]
        ? above_closed : m[MI_CAL_FOLLOWER_CAP];
    uint16_t requested = (uint16_t)desired * 256u, old = word(m, MI_FOLLOWER);
    uint16_t next = requested > old ? requested : sub(old, word(m, MI_CAL_FOLLOWER_DECAY));
    if (next < requested) next = requested;
    put(m, MI_SCRATCH, requested);
    put(m, MI_FOLLOWER, next); put(m, 0x0880, next);
}

static void pi(uint8_t *m)
{
    put(m, MI_P_WORD, 0); m[0x086d] = 0;
    bool proportional_admitted = (m[0x36] & 4u) ||
        (m[0x01d9] <= m[MI_CAL_TPS_EXIT] && (m[0x36] & 0x80u));
    if (proportional_admitted && !(m[0x46] & 8u) && m[MI_ERROR] > m[MI_CAL_DEADBAND]) {
        unsigned e = m[MI_ERROR] - m[MI_CAL_DEADBAND];
        m[0x0864] = (uint8_t)e;
        uint16_t p = (uint16_t)(e * m[MI_CAL_KP]);
        if (p > word(m, MI_CAL_P_LIMIT)) p = word(m, MI_CAL_P_LIMIT);
        put(m, MI_P_WORD, p); m[0x086d] = (uint8_t)(p >> 8);
        if ((m[0x36] & 8u) && !(m[0x3e] & 4u) && !m[MI_START_AIR] && !word(m, MI_FOLLOWER)) {
            uint16_t old = word(m, MI_INTEGRAL), next = old;
            if (m[0x36] & 0x80u) {
                if (word(m, 0x0889) != 0) {
                    uint16_t amount = (uint16_t)(e * m[MI_CAL_KI_DOWN]);
                    put(m, MI_SCRATCH, amount); next = sub(old, amount);
                }
            } else if (word(m, 0x0889) != 65535u) {
                uint32_t sum = (uint32_t)old + e * m[MI_CAL_KI_UP];
                if (sum <= 65535u) put(m, MI_SCRATCH, (uint16_t)sum);
                next = sum > word(m, MI_CAL_I_LIMIT) ? word(m, MI_CAL_I_LIMIT) : (uint16_t)sum;
            }
            put(m, MI_INTEGRAL, next);
        }
    }
    uint16_t integral = word(m, MI_INTEGRAL);
    put(m, 0x0862, integral); m[0x086a] = (uint8_t)(integral >> 8);
}

static uint16_t compose(uint8_t *m)
{
    m[0x086c] = curve(m, MI_CAL_COLD_AIR, m[0x0283]);
    uint32_t total = cap(word(m, MI_INTEGRAL) + (uint32_t)m[0x086c] * 256u);
    total = cap(total + (uint32_t)m[MI_START_AIR] * 256u);
    if (m[0x52] & 0x20u) total = cap(total + (uint32_t)m[MI_CAL_AC_AIR] * 256u);
    if (m[0x36] & 0x80u) total = sub((uint16_t)total, word(m, MI_P_WORD));
    else total = cap(total + word(m, MI_P_WORD));
    if (m[0x36] & 0x10u) total += (uint32_t)m[MI_CAL_STALL_AIR] * 256u;
    uint16_t flow = cap(total), old = word(m, 0x087d);
    put(m, MI_SCRATCH, flow);
    uint8_t ae = 0;
    if (flow >= old) {
        uint16_t difference = flow - old;
        m[0x086b] = (uint8_t)(difference >> 8);
        if (m[0x01d9] < m[0x50a9] && (difference >> 8) >= m[0x50a8])
            ae = scaled(m, 0x50a2, (uint8_t)(cap(4u * (uint32_t)difference) >> 8));
    }
    m[0x087f] = ae; put(m, 0x087d, flow);
    return cap((uint32_t)flow + word(m, MI_FOLLOWER));
}

uint16_t mi_stopped(uint8_t m[65536])
{ mi_init(m); mi_target(m); return compose(m); }

uint16_t mi_run(uint8_t m[65536])
{
    if (m[MI_SIGNATURE] != 0xa5) mi_init(m);
    mi_target(m); follow(m);
    if (m[MI_START_AIR]) {
        --m[MI_START_DIV];
        if (!m[MI_START_DIV]) { m[MI_START_DIV] = m[MI_CAL_START_DIV]; --m[MI_START_AIR]; }
    }
    m[0x36] &= 0x6cu;
    if (m[0x52] & 0x20u) m[0x36] |= 1u;
    uint8_t target = m[0x0857], rpm = m[0x63];
    if (rpm >= target) m[0x36] |= 0x80u;
    m[MI_ERROR] = rpm >= target ? rpm - target : target - rpm;
    put(m, 0x0859, (uint16_t)m[MI_ERROR] * 256u);
    bool retained = (m[0x36] & 4u) != 0;
    unsigned threshold = (unsigned)target + m[retained ? MI_CAL_RPM_EXIT : MI_CAL_RPM_ENTER];
    bool captured = m[0x01d9] <= m[retained ? MI_CAL_TPS_EXIT : MI_CAL_TPS_ENTER] && rpm <= threshold;
    if (captured) {
        m[0x36] |= 4u;
        if (m[MI_QUALIFY] < m[MI_CAL_QUALIFY]) ++m[MI_QUALIFY];
        if (m[MI_QUALIFY] >= m[MI_CAL_QUALIFY]) m[0x36] |= 8u;
    } else { m[0x36] &= (uint8_t)~0x0cu; m[MI_QUALIFY] = 0; }
    if (m[0x46] & 8u) { m[0x36] &= (uint8_t)~8u; m[MI_QUALIFY] = 0; }
    if ((m[0x36] & 4u) && rpm < m[0x0868]) m[0x36] |= 0x10u;
    pi(m);
    return compose(m);
}
