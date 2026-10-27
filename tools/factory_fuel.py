"""Exact bounded BMHM running-fuel integer/state model, independent of the CPU.

Inputs are a 64K memory snapshot plus coherent device word samples by read PC.
The model starts at normalized speed-density inputs ($7FD8), and ends before
$852C's later producers. Calibrations and RAM stay stable during the slice.
No physical injector transfer function or arbitrary interrupt is simulated.
"""
from __future__ import annotations


def u8(v):return v & 255
def u16(v):return v & 65535
def sat16(v):return min(v,65535)
def multiply(a,w):return (a*w+128)>>8
def fraction(n,d):return 65535 if not d or n>=d else (n<<16)//d
def rounded_byte(w):return min(255,(w+128)>>8)


def interpolate(first,second,fraction256):
    adjustment=(abs(second-first)*fraction256+128)>>8
    return first+adjustment if second>=first else first-adjustment


def base_values(density,temperature,volume,ve,period,afr,flow):
    """Keep each quotient truncation and the saturated fractional divides."""
    displaced=multiply(volume,fraction(density,temperature))
    air=multiply(ve,displaced)
    rate=65535 if not period else min(65535,2*((air<<8)//period))
    mixture=fraction(air>>2,afr<<8)
    pulse=65535 if not flow else min(65535,(mixture<<8)//flow)
    return {"displaced":displaced,"air":air,"air_rate":rate,"mixture_quotient":mixture,"pulse":pulse}


class FuelModel:
    def __init__(self,memory,samples=None):
        if len(memory)!=65536:raise ValueError("Fuel model requires a 64K snapshot")
        self.mem=bytearray(memory);self.samples=samples or {};self.writes=[];self.stages=[]

    def b(self,a):return self.mem[a]

    def w(self,a,pc=None):
        sampled=self.samples.get(pc,{})
        return sampled[a] if a in sampled else (self.b(a)<<8)|self.b(a+1)

    def put(self,pc,a,value,bits=8):
        value &= (1<<bits)-1
        if bits==16:self.mem[a:a+2]=value.to_bytes(2,"big")
        else:self.mem[a]=value
        self.writes.append((pc,a,value,bits))

    def flag(self,pc,a,mask,on):
        self.put(pc,a,(self.b(a)|mask) if on else (self.b(a)&~mask))

    def lookup(self,a,base,offset=0):
        a=max(a-offset,0);index=a>>4;f=(a&15)<<4
        return interpolate(self.b(base+index),self.b(base+index+1),f)

    def header_lookup(self,a,base,offset=0):
        return self.lookup(min(a,self.b(base)),base+1,offset)

    def lookup2(self,a,b,base):
        a=max(a-self.b(base),0);b=max(b-self.b(base+1),0)
        stride=self.b(base+2);row,col=a>>4,b>>4;fcol=(b&15)<<4
        cell=base+3+row*stride+col
        first=interpolate(self.b(cell),self.b(cell+1),fcol)
        second=interpolate(self.b(cell+stride),self.b(cell+stride+1),fcol)
        return interpolate(first,second,(a&15)<<4)

    def base(self):
        self.stages.append("base")
        result=base_values(self.w(0x0257),self.w(0x0236),self.b(0x4D94),self.b(0x0231),
                           self.w(0x01E8),self.b(0x024A),self.w(0x4D92))
        for pc,a,key in [(0x7FE8,0x0238,"displaced"),(0x7FF4,0x0234,"air"),
                         (0x800D,0x0232,"air_rate"),(0x802F,0x024E,"pulse")]:self.put(pc,a,result[key],16)
        return result

    def scale_pulse(self,multiplier,double=False):
        pulse=self.w(0x024E)
        if double:
            pulse=sat16(pulse*2);self.put(0x80F8,0x024E,pulse,16)
        self.put(0x8102,0x024E,multiply(multiplier,pulse),16)

    def egr_and_blm(self):
        self.stages.append("EGR_BLM")
        m=u16(self.w(0x01B2)+128)>>8
        correction=multiply(m,self.w(0x024E))>>2
        self.put(0x8040,0x0252,correction,16)
        self.put(0x8049,0x024E,self.w(0x024E)-correction,16)
        blm=self.b(0x0248)
        if blm>=128 or not self.b(0x3D)&0x20:self.scale_pulse(blm,True)

    def reduce_cut(self):
        self.stages.append("decel_reduction")
        self.flag(0x821D,0x46,8,True)
        self.put(0x8223,0x0245,self.b(0x4942))
        self.flag(0x8226,0x3D,0x10,True)
        m=max(self.b(0x0244)-self.b(0x4943),0)
        self.put(0x8232,0x0244,m);self.scale_pulse(m)

    def clear_enlean(self):
        self.flag(0x82E7,0x3D,0x10,False);self.flag(0x82EA,0x53,2,False)

    def ordinary_decel(self):
        self.flag(0x824D,0x46,8,False);self.put(0x8252,0x0244,255)
        tps=rounded_byte(self.w(0x01DE))-self.b(0x01D9)
        if tps<0:self.clear_enlean();return
        self.put(0x8266,0x082B,tps)
        if not (self.b(0x400B)&128 and self.b(0x53)&2):
            if tps<=self.b(0x4936):self.clear_enlean();return
            self.flag(0x827C,0x53,2,True)
        load=rounded_byte(self.w(0x01C7))-self.b(0x01C0)
        if load<0 or load<=self.b(0x4937):self.clear_enlean();return
        a=min(255,self.lookup(min(load,160),0x4B20)+self.lookup(tps,0x4B2B))
        a=min(255,(a*self.b(0x0242)*8)>>8)
        if self.b(0x0284)<self.b(0x4939):a=sat16(2*(a*self.b(0x4938)+64))>>8
        multiplier=u8(-a)
        if not multiplier:self.clear_enlean();return
        self.stages.append("decel_enlean")
        self.flag(0x82D4,0x3D,0x10,True)
        self.put(0x82DE,0x023A,multiply(multiplier,self.w(0x023A)),16)
        self.scale_pulse(multiplier)

    def async_enrichment(self):
        a=self.b(0x087F)
        if self.b(0x3E)&1:
            self.flag(0x8113,0x3E,1,False);a+=self.b(0x48C6)
        if a<=255:
            if not self.b(0x41)&0x10:self.flag(0x811F,0x41,8,False)
            elif not self.b(0x41)&8:
                self.flag(0x8128,0x41,8,True);a+=self.b(0x48C7)
            if a<=255:a+=self.b(0x023F)
        a=min(a,255)
        if a:
            self.put(0x8149,0x023A,self.w(0x023A)+((a*self.b(0x023C))>>3),16)
        if a or self.b(5)&128:
            if not self.b(0x3D)&0x40:self.flag(0x8150,0x6E,8,True)
            self.flag(0x8153,0x3D,0xC0,True);self.flag(0x8156,0x6E,1,True)
            self.flag(0x8159,0x44,2,True);self.put(0x815F,0x081D,self.b(0x48CA))
        else:
            self.flag(0x8164,0x3D,0x40,False)
            timer=self.b(0x081D)
            if timer:self.put(0x816D,0x081D,timer-1)
            else:self.flag(0x8172,0x44,2,False)

    def decel_mode(self):
        """Return reduce/recover/reset/delay from the $8175-$824A gates."""
        if self.b(6)<self.b(0x4944):return "ordinary"
        if self.b(0x41)&0x20:return "recover"
        if not self.b(0x6F)&0x24 and self.header_lookup(self.b(0x62),0x4C94,32)<=self.b(0x01D9):
            if self.b(0x46)&8:self.flag(0x819C,0x3E,1,True)
            return "reset"
        if self.b(0x65)>self.b(0x63) and self.b(0x65)-self.b(0x63)>self.b(0x4945):return "recover"
        if not self.b(0x6F)&0x48:
            if self.b(0x01CA)>self.b(0x4946):return "recover"
            load=self.b(0x01CF) if self.b(0x400E)&2 else self.b(0x01C0)
            if load>=self.b(0x493D) and (not self.b(0x46)&8 or load>=self.b(0x493E)):return "reset_load"
        threshold=self.b(0x0243)
        if not self.b(0x46)&8:threshold=min(255,threshold+self.b(0x493A))
        if threshold>=self.b(0x62):return "recover"
        if not self.b(0x16)&0x10 and self.b(0x0284)<self.b(0x493C if self.b(0x46)&8 else 0x493B):return "recover"
        return "delay" if self.b(0x0246) else "reduce"

    def controls(self):
        self.stages.append("control_gates")
        # $8058-$8099: conditional cut qualification with a countdown/hysteresis.
        if not self.b(0x16)&0x10:
            evaluate=True
            if not self.b(0x400F)&128:
                a=self.b(0x5155)
                if not self.b(0x41)&0x20:
                    a=self.b(0x084D)
                    if not a:evaluate=False
                    else:a-=1
                if evaluate:self.put(0x8070,0x084D,a)
            if (evaluate and self.b(0x0812)<=self.b(0x5156) and self.b(0x01D9)>self.b(0x5159)):
                threshold=self.b(0x5158 if self.b(0x53)&8 else 0x5157)
                if threshold<self.b(0x61):
                    self.flag(0x8096,0x53,8,True);self.reduce_cut();return
                self.flag(0x8091,0x53,8,False)
        # $809C-$8109: threshold selection, delay, and explicit zero of PW.
        clear_counter=True;cut=False
        if not (self.b(0x400F)&1 and not self.b(0x6F)&0x34):
            hysteresis=bool(self.b(0x46)&0x10)
            x=0x4967+int(hysteresis)+(2 if self.b(0x16)&0x10 or self.b(0x99)&3 else 0)
            y=0x496B+int(hysteresis)
            cut=self.b(0x62)>self.b(x)
            if not cut and self.b(0x0284)>self.b(y) and self.b(0x62)>self.b(0x4966):
                if self.b(0x026A)>=self.b(0x4965):cut=True
                else:self.put(0x80DD,0x026A,self.b(0x026A)+1);clear_counter=False
        if cut:
            self.stages.append("hard_zero")
            self.flag(0x80E2,0x46,0x10,True);self.put(0x80E8,0x024E,0,16)
            self.reduce_cut();return
        if clear_counter:self.put(0x8106,0x026A,0)
        self.flag(0x8109,0x46,0x10,False)
        self.async_enrichment()
        mode=self.decel_mode();self.stages.append(mode)
        if mode=="reduce":self.reduce_cut();return
        if mode=="recover":
            if self.b(0x0245):
                total=self.w(0x023A)+self.w(0x493F)
                self.put(0x81F7,0x023A,0x7FFF if total>65535 else total,16)
                self.flag(0x81FA,0x3D,128,True)
            self.put(0x81FD,0x0245,0)
        elif mode=="reset":self.put(0x81FD,0x0245,0)
        if mode in {"recover","reset","reset_load"}:self.put(0x8242,0x0246,self.b(0x4941))
        elif mode=="delay":
            a=self.b(0x0246)-(not bool(self.b(2)&14));self.put(0x8242,0x0246,a)
        if mode!="ordinary" and self.b(0x0245):self.put(0x824A,0x0245,self.b(0x0245)-1)
        self.ordinary_decel()

    def int_producer(self):
        proportional=self.b(0x027A)
        if self.b(0x3E)&0x40:
            if self.b(0x400B)&8 and self.b(0x44)&2 and self.b(0x4912)<proportional:
                proportional=self.b(0x4912);self.put(0x8903,0x027A,proportional)
            combined=max(0,self.b(0x020F)-proportional)
        else:combined=min(255,self.b(0x020F)+proportional)
        self.put(0x891A,0x026F,combined-128)

    def offset_producer(self):
        self.put(0xE303,0x0256,self.lookup(self.b(0xA7),0x4B05))

    def rpm_correction(self):
        self.stages.append("RPM_correction")
        if (self.b(0x67)<self.b(0x4516) or self.b(0x01D9)>self.b(0x48DB)
                or self.b(0x0284)>self.b(0x48DC) or self.b(6)<self.b(0x48DD)):
            self.put(0x830D,0x6C,128);return
        a=rounded_byte(fraction(self.w(0x6A)>>1,self.w(0x68)))
        self.put(0x831F,0x6C,a)
        a=self.b(0x451A) if a>=self.b(0x451A) else max(a,self.b(0x4519))
        self.put(0x833F,0x024E,sat16(2*multiply(a,self.w(0x024E))),16)

    def additive(self):
        correction=self.b(0x026F)
        correction=correction-256 if correction&128 else correction
        self.put(0x839C,0x024E,min(65535,max(0,self.w(0x024E)+correction)),16)
        pulse=sat16(self.w(0x024E)+self.b(0x023E))
        self.put(0x83AB,0x024E,pulse,16);self.put(0x83AE,0x0254,pulse,16)

    def environment(self):
        self.stages.append("baro_battery_INT_AE")
        a=(min(self.b(0x01C6),216)*151+145)>>8
        correction=self.lookup2(a,self.b(0x01CC),0x49AA)
        self.put(0x836C,0x024E,sat16(4*multiply(correction,self.w(0x024E))),16)
        correction=self.lookup(self.b(0x55),0x4988)
        self.put(0x837D,0x024E,multiply(correction,self.w(0x024E)),16)
        self.additive()

    def emit_async(self,pulse):
        self.stages.append("async_emit")
        if self.b(0x400E)&0x10 and pulse<256:
            pulse=max(0,pulse+self.lookup(pulse,0x4979,32)-self.w(0x4971))
        self.put(0x8571,0x3FF2,pulse+self.b(0x0256),16)
        feedback=self.w(0x3FFC,0x8577)&0xFBFF
        self.put(0x857F,0x3FFC,feedback,16)
        self.put(0x8587,0x3FFC,feedback|0x0400,16)

    def async_packet(self):
        total=u16(self.w(0x0259)+self.w(0x023A))
        maximum,minimum=self.w(0x4932),self.w(0x4934)
        if total<=maximum:
            if total<=minimum:
                self.flag(0x84B6,0x46,1,True);self.flag(0x84B9,0x3D,128,False);return
            self.put(0x848B,0x023A,0,16);self.put(0x848E,0x0259,0,16)
            pulse=total
        else:
            difference=self.w(0x0259)-maximum
            if difference<0:
                self.put(0x849E,0x023A,difference+self.w(0x023A),16);difference=0
            self.put(0x84A3,0x0259,difference,16);pulse=maximum
        self.emit_async(pulse)
        self.flag(0x84AE,0x3D,128,True);self.flag(0x84B1,0x46,1,False)

    def route(self):
        self.stages.append("delivery_route")
        if self.b(0x44)&0x10:
            self.put(0x83B7,0x024E,0,16);return
        if self.b(0x400B)&1:
            double=bool(self.b(0x51)&1)
            if not double:
                if self.b(0x082A)<255:self.put(0x83D1,0x082A,self.b(0x082A)+1)
                if self.w(0x0254)<=self.w(0x492C) and self.b(0x082A)>=self.b(0x4974):
                    self.flag(0x83E7,0x51,1,True);self.flag(0x83EA,0x3F,0x10,True);double=True
            if double:self.put(0x83F6,0x024E,sat16(2*self.w(0x024E)),16)
            if self.b(0x3D)&128:self.async_packet()
            return
        synchronous=bool(self.b(0x400B)&4 and self.b(0x50)&128)
        if not synchronous:
            base=0x492A if self.b(0x3E)&0x10 else 0x492C
            self.flag(0x840F,0x3E,0x10,True)
            thresholds=self.w(base+4)
            synchronous=(self.w(base)<self.w(0x024E)
                         and ((thresholds>>8)>=self.b(0x01C0) or (thresholds&255)>=self.b(0x62)))
        if synchronous:
            self.flag(0x8469,0x3E,0x10,False);self.put(0x846F,0x0259,0,16)
            if self.b(0x3D)&128:self.async_packet()
            return
        self.stages.append("TBI_async_route")
        self.put(0x8426,0x3FCE,0,16)
        ratio=fraction(self.w(0x024E),sat16(2*self.w(0x3FC0,0x842C)))
        integer,remainder=divmod(ratio,80)
        fractional=(remainder<<16)//80
        rounded=fractional+128
        self.put(0x8449,0x025E,(rounded>>8)&255)
        integer+=int(rounded>65535)
        self.put(0x8452,0x025C,integer,16)
        total=self.w(0x025A)+self.w(0x025D)
        self.put(0x845B,0x025A,total,16)
        self.put(0x8464,0x0259,self.b(0x0259)+self.b(0x025C)+int(total>65535))
        self.async_packet()

    def shape(self):
        """$84BC-$852B, including bypass and CPI's alternative output."""
        self.stages.append("final_shape")
        pulse=self.w(0x024E)
        if self.b(0x3E)&0x10:
            self.put(0x84C3,0x024C,pulse,16);self.flag(0x84C6,0x3F,128,False);return
        if pulse:
            borrowed=False
            if pulse<256:
                pulse+=self.lookup(pulse,0x4979,32)
                borrowed=pulse<self.w(0x4971);pulse=u16(pulse-self.w(0x4971))
            if not borrowed:
                self.flag(0x84E6,0x3F,128,False)
            if borrowed or pulse<self.w(0x496D):
                self.flag(0x84EF,0x3F,128,True);pulse=self.w(0x496F)
        self.finish(pulse)

    def finish(self,pulse):
        self.put(0x84F5,0x024C,pulse,16)
        final=min(u16(pulse+self.b(0x0256)),32767) if pulse else 0
        self.put(0x8508,0x0250,final,16)
        if not self.b(0x400B)&1:self.put(0x8512,0x3FCE,final,16)
        else:self.put(0x8529,0x081F,sat16(4*multiply(self.b(0x4973),self.w(0x005F))),16)

    def run(self,start=0x7FD8):
        stages=[(0x7FD8,self.base),(0x8032,self.egr_and_blm),(0x8058,self.controls),
                (0x82ED,self.rpm_correction),(0x8342,self.environment),
                (0x83B1,self.route),(0x84BC,self.shape)]
        addresses=[a for a,_ in stages]
        if start not in addresses:raise ValueError("Entry must be a reviewed fuel stage boundary")
        for _,stage in stages[addresses.index(start):]:stage()
        return self
