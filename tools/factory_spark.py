"""Exact unsigned machine-word models for bounded BMHM spark ROM paths.

Addresses identify the verified instructions. Physical units and ASIC behavior
are separate from the integer transformations. Device readbacks at different
PCs are explicit inputs; no immutable-counter or atomic-snapshot assumption.
"""
from __future__ import annotations

from dataclasses import dataclass


def u16(value):return value & 0xFFFF
def u8(value):return value & 0xFF


def rounded_multiply(multiplier,word):
    return (multiplier*word+128)>>8


def period_basis(raw_period,calibration_4141):
    multiplier=u8(calibration_4141*32)
    return raw_period if multiplier==0 else rounded_multiply(multiplier,raw_period)


def decay_adaptive(previous):
    result=u16(previous-(previous>>3)-1)
    return 0 if result & 0x8000 else result


def reference_term(period):
    """A6B8-A6D9: all 65,536 raw input words have a defined result."""
    if period<458:return (period>>1)+79
    if period<1638:return ((period-458)>>4)+308
    return ((period-458)>>2)+87


@dataclass(frozen=True)
class TermInputs:
    period: int
    previous_period: int
    adaptive: int
    load_now: int
    load_old: int
    load_latch: int
    battery: int
    limit_period: int


def spark_terms(inputs):
    p=inputs.period; adaptive=inputs.adaptive;writes=[]
    delta=u8(inputs.load_now-inputs.load_old)
    if inputs.load_now>=inputs.load_old and delta>=32:
        candidate=0xFF00|delta
        adaptive=candidate;writes.append((0xA6A4,0x01EA,candidate,16))
    else:
        candidate=u16((inputs.previous_period-p)*2)
        difference=u16(candidate-adaptive)
        if not difference & 0x8000:
            adaptive=candidate;writes.append((0xA6A4,0x01EA,candidate,16))
    cap=p>>3
    if adaptive>cap:
        adaptive=cap;writes.append((0xA6B5,0x01EA,cap,16))
    writes.append((0xA6BB,0x01E6,p,16))
    base=reference_term(p);writes.append((0xA6D9,0x083F,base,16))
    summed=u16(4*max(120-inputs.battery,0)+base+adaptive)
    writes.append((0xA6EC,0x01EC,summed,16))
    limit=u16(inputs.limit_period-39)
    correction=min(summed,limit)
    if summed>limit:writes.append((0xA6FD,0x01EC,limit,16))
    writes.append((0xA703,0x01C2,inputs.load_latch,8))
    return {"adaptive":adaptive,"reference_term":base,"correction":correction,
            "previous_period":p,"load_old":inputs.load_latch,"writes":writes}


def latency_lookup(rpm_count,table):
    """F499 entry: max header, 16-count cells, rounded absolute difference."""
    a=min(rpm_count,table[0]);index=a>>4;fraction=(a&15)<<4
    first,second=table[1+index:3+index]
    adjustment=(abs(second-first)*fraction+128)>>8
    return first+adjustment if second>=first else first-adjustment


@dataclass(frozen=True)
class HandoffInputs:
    command: int = 0
    startup: int = 0
    startup_bypass: bool = True
    rpm: int = 0
    basis: int = 0
    anchor_period: int = 0
    rolling1: int = 0
    rolling2: int | None = None
    work_read: int = 0
    correction1: int = 0
    correction2: int | None = None
    flags4f: int = 0
    headsup: bool = False


def bridge(saved,period,rolling1,rolling2,work_read,correction1,correction2):
    anchor=(u16(-period)>>4)|0xF000
    candidate=u16(anchor+rolling1)
    difference=u16(candidate-saved)
    chosen=saved if difference & 0x8000 else candidate
    first=u16(chosen-rolling2)
    second=u16(first+work_read-correction1)
    writes=[(0xABAA,0x3FE8,first),(0xABBA,0x3FE6,second),
            (0xABC0,0x3FDC,correction2),(0xABC8,0x3FF6,chosen)]
    return {"saved_input":saved,"anchor":anchor,"candidate":candidate,"difference":difference,
            "replacement":not bool(difference&0x8000),"chosen":chosen,"writes":writes}


def spark_handoff(inputs,latency_table):
    if inputs.headsup:
        raise ValueError("$AB66 calls external $180F when $0086 bit6 is set; a hook contract is required")
    negative=bool(inputs.command & 0x8000)
    magnitude=u8(-u8(inputs.command)) if negative else u8(inputs.command)
    if not inputs.startup_bypass:
        multiplier=u8((inputs.startup>>8)+bool(inputs.startup&0x80))
        magnitude=u8(((magnitude*multiplier)>>8)+1)
    latency=latency_lookup(inputs.rpm,latency_table)
    product=rounded_multiply(magnitude,inputs.basis)
    saved=u16((product if negative else -product)-latency)
    result=bridge(saved,inputs.anchor_period,inputs.rolling1,
                  inputs.rolling1 if inputs.rolling2 is None else inputs.rolling2,
                  inputs.work_read,inputs.correction1,
                  inputs.correction1 if inputs.correction2 is None else inputs.correction2)
    result.update({"magnitude":magnitude,"latency":latency,"time_product":product,
                   "flags4f":(inputs.flags4f&0xFE)|int(negative),
                   "ram_state":{0x01EE:inputs.command,0x01F0:inputs.command,0x0201:latency}})
    return result
