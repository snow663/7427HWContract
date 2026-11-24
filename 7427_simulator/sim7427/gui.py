"""Clickable engineering workbench for the new ROM simulator."""
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path
from .machine import Machine

VECTOR_NAMES = {
    "IRQ (REF)  FFF2":0xFFF2,
    "TOC3       FFE4":0xFFE4,
    "SCI        FFD6":0xFFD6,
    "OC1        FFE8":0xFFE8,
    "SWI        FFF6":0xFFF6,
}

def number(value: str) -> int:
    s=value.strip()
    return int(s[1:],16) if s.startswith("$") else int(s,0)

class Workbench:
    def __init__(self, root: tk.Tk):
        self.root=root
        self.sim=Machine()
        self.running=False
        self.last_trace=0
        self.path=None
        root.title("7427 Firmware Simulator | Fresh Implementation v0.1")
        root.geometry("1100x740")
        root.minsize(850,580)
        self.status=tk.StringVar(value="Load a 32/48/64 KiB BIN. The HC11 ISA is incremental.")
        self.path_label=tk.StringVar(value="No ROM loaded")
        self.regs=tk.StringVar()
        self.mem_addr=tk.StringVar(value="$0000")
        self.mem_size=tk.StringVar(value="128")
        self.addr_write=tk.StringVar(value="$0042")
        self.value_write=tk.StringVar(value="$00")
        self.break_addr=tk.StringVar(value="$7100")
        self.irq_choice=tk.StringVar(value=next(iter(VECTOR_NAMES)))
        self.batch=tk.StringVar(value="500")
        self.inputs={k:tk.StringVar(value=str(v))
                     for k,v in self.sim.engine_inputs.items()}
        self.build()
        self.refresh()
        root.protocol("WM_DELETE_WINDOW",self.close)

    def build(self):
        root=self.root
        root.columnconfigure(0,weight=1)
        root.rowconfigure(2,weight=1)
        bar=ttk.Frame(root,padding=7)
        bar.grid(row=0,column=0,sticky="ew")
        for label,fn in (("Load BIN",self.load),("Reset",self.reset),
                         ("Step",self.step),("Run",self.toggle),
                         ("Pause",self.pause)):
            ttk.Button(bar,text=label,command=fn).pack(side="left",padx=3)
        ttk.Label(bar,text="Batch:").pack(side="left",padx=(15,2))
        ttk.Entry(bar,textvariable=self.batch,width=7).pack(side="left")
        ttk.Label(bar,textvariable=self.path_label).pack(side="right")
        ttk.Label(root,textvariable=self.status,relief="groove",anchor="w",
                  padding=5).grid(row=1,column=0,sticky="ew")
        split=ttk.Panedwindow(root,orient="horizontal")
        split.grid(row=2,column=0,sticky="nsew",padx=5,pady=5)
        left=ttk.Frame(split,padding=4)
        right=ttk.Frame(split,padding=4)
        split.add(left,weight=2)
        split.add(right,weight=3)
        self.left(left)
        self.right(right)
        foot=ttk.Label(root,text=("Engineering model: raw input controls are NOT"
                    " connected to ADC pins until source-verified. Unsupported opcodes halt."),
                    padding=5,anchor="w")
        foot.grid(row=3,column=0,sticky="ew")

    def left(self,parent):
        parent.columnconfigure(0,weight=1)
        parent.rowconfigure(1,weight=1)
        ttk.Label(parent,text="CPU STATE",font=("TkDefaultFont",11,"bold")).grid(
            row=0,column=0,sticky="w")
        ttk.Label(parent,textvariable=self.regs,font=("Courier",10),
                  justify="left").grid(row=1,column=0,sticky="nw")
        bp=ttk.LabelFrame(parent,text="Breakpoints / IRQ",padding=7)
        bp.grid(row=2,column=0,sticky="ew",pady=8)
        ttk.Entry(bp,textvariable=self.break_addr,width=12).grid(row=0,column=0)
        ttk.Button(bp,text="Toggle breakpoint",command=self.breakpoint).grid(
            row=0,column=1,padx=3)
        ttk.Combobox(bp,textvariable=self.irq_choice,values=list(VECTOR_NAMES),
                     state="readonly",width=17).grid(row=1,column=0,sticky="ew",pady=4)
        ttk.Button(bp,text="Inject IRQ",command=self.inject_irq).grid(row=1,column=1)
        inputs=ttk.LabelFrame(parent,text="Engine controls (unbound until verified)",padding=7)
        inputs.grid(row=3,column=0,sticky="ew")
        for i,(name,var) in enumerate(self.inputs.items()):
            ttk.Label(inputs,text=name).grid(row=i,column=0,sticky="w")
            ttk.Entry(inputs,textvariable=var,width=12).grid(row=i,column=1,pady=2)
        ttk.Button(inputs,text="Store test values",command=self.set_inputs).grid(
            row=len(self.inputs),column=0,columnspan=2,sticky="ew",pady=4)

    def right(self,parent):
        parent.columnconfigure(0,weight=1)
        parent.rowconfigure(1,weight=1)
        parent.rowconfigure(3,weight=1)
        tools=ttk.Frame(parent)
        tools.grid(row=0,column=0,sticky="ew")
        ttk.Label(tools,text="Memory $").pack(side="left")
        ttk.Entry(tools,textvariable=self.mem_addr,width=9).pack(side="left")
        ttk.Label(tools,text="bytes").pack(side="left",padx=4)
        ttk.Entry(tools,textvariable=self.mem_size,width=5).pack(side="left")
        ttk.Button(tools,text="Inspect",command=self.inspect).pack(side="left",padx=5)
        self.memory=scrolledtext.ScrolledText(parent,height=13,font=("Courier",10))
        self.memory.grid(row=1,column=0,sticky="nsew",pady=4)
        edits=ttk.Frame(parent)
        edits.grid(row=2,column=0,sticky="ew")
        ttk.Label(edits,text="Write:").pack(side="left")
        ttk.Entry(edits,textvariable=self.addr_write,width=10).pack(side="left")
        ttk.Entry(edits,textvariable=self.value_write,width=8).pack(side="left")
        ttk.Button(edits,text="Write RAM/I-O",command=self.write_memory).pack(
            side="left",padx=6)
        ttk.Button(edits,text="Patch ROM (session)",command=self.patch).pack(
            side="left")
        tracebox=ttk.LabelFrame(parent,text="Recent register / output writes",padding=4)
        tracebox.grid(row=3,column=0,sticky="nsew",pady=5)
        tracebox.rowconfigure(0,weight=1)
        tracebox.columnconfigure(0,weight=1)
        self.trace=scrolledtext.ScrolledText(tracebox,font=("Courier",9),height=12)
        self.trace.grid(row=0,column=0,sticky="nsew")

    def refresh(self):
        r=self.sim.cpu.r
        self.regs.set(
            f" PC  ${r.pc:04X}    SP  ${r.sp:04X}\n"
            f" A   ${r.a:02X}      B   ${r.b:02X}\n"
            f" D   ${r.d:04X}    X   ${r.x:04X}\n"
            f" Y   ${r.y:04X}    CCR ${r.ccr:02X}\n"
            f" HC11 REG BASE ${self.sim.bus.register_base:04X}\n"
            f" Instructions  {self.sim.cpu.instructions:,}\n"
            f" Breakpoints   {len(self.sim.breakpoints)}"
        )
        self.inspect(silent=True)
        self.trace.delete("1.0","end")
        for item in list(self.sim.events)[-120:]:
            self.trace.insert("end",
                f"{item.direction:<18} ${item.address:04X} "
                f"${item.value:02X} {item.region}\n")
        self.trace.see("end")

    def load(self):
        name=filedialog.askopenfilename(filetypes=[("PCM ROM","*.bin *.BIN"),
                                                   ("All files","*.*")])
        if not name:return
        try:
            self.sim.load_rom(name)
            self.path=Path(name)
            self.path_label.set(self.path.name)
            self.status.set(f"Loaded {self.path.name}; SHA256 {self.sim.last_rom_sha256[:16]}...")
            self.refresh()
        except Exception as e:self.error(e)

    def reset(self):
        self.pause()
        self.sim.reset()
        self.status.set("CPU reset; PC from $FFFE")
        self.refresh()

    def step(self):
        self.pause()
        result=self.sim.step()
        self.status.set(f"{result.reason}: PC ${result.pc:04X} {result.detail}")
        self.refresh()

    def toggle(self):
        if not self.sim.bus.rom_loaded:
            self.status.set("Load BIN first");return
        if self.running:return
        self.running=True
        self.tick()

    def tick(self):
        if not self.running:return
        try:
            n=number(self.batch.get())
            result=self.sim.run(max(1,min(n,25000)))
            self.status.set(f"{result.reason}: {result.instructions} steps, "
                            f"PC ${result.pc:04X} {result.detail}")
            self.refresh()
            if result.reason=="limit":
                self.root.after(1,self.tick)
            else:self.running=False
        except Exception as e:
            self.running=False
            self.error(e)

    def pause(self):
        self.running=False

    def breakpoint(self):
        try:
            addr=number(self.break_addr.get())
            if not 0<=addr<=0xFFFF:raise ValueError("Bad breakpoint address")
            if addr in self.sim.breakpoints:self.sim.breakpoints.remove(addr)
            else:self.sim.breakpoints.add(addr)
            self.refresh()
        except Exception as e:self.error(e)

    def inject_irq(self):
        try:
            addr=VECTOR_NAMES[self.irq_choice.get()]
            accepted=self.sim.irq(addr,maskable=(addr!=0xFFF6))
            self.status.set(f"Vector ${addr:04X}: "
                            +("admitted" if accepted else "masked/unloaded"))
            self.refresh()
        except Exception as e:self.error(e)

    def set_inputs(self):
        try:
            values={k:float(v.get()) for k,v in self.inputs.items()}
            self.sim.engine_inputs.update(values)
            self.status.set("Virtual engine input values stored; no unverified ADC routing")
        except Exception as e:self.error(e)

    def inspect(self,silent=False):
        try:
            a=number(self.mem_addr.get())
            n=number(self.mem_size.get())
            self.memory.delete("1.0","end")
            self.memory.insert("end",self.sim.memory_dump(a,min(n,4096)))
        except Exception as e:
            if not silent:self.error(e)

    def write_memory(self):
        try:
            self.sim.write_memory(number(self.addr_write.get()),
                                  number(self.value_write.get()))
            self.status.set("CPU-visible memory write applied")
            self.refresh()
        except Exception as e:self.error(e)

    def patch(self):
        if not messagebox.askyesno("Session-only patch",
            "Patch simulated ROM memory? The BIN file is not changed."):
            return
        try:
            self.sim.bus.patch_rom(number(self.addr_write.get()),
                                   number(self.value_write.get()))
            self.status.set("In-memory ROM patch only; disk image unchanged")
            self.refresh()
        except Exception as e:self.error(e)

    def error(self,exc):
        self.status.set(str(exc))
        messagebox.showerror("Simulator",str(exc))

    def close(self):
        self.pause()
        self.root.destroy()

def main():
    root=tk.Tk()
    Workbench(root)
    root.mainloop()

if __name__=="__main__":
    main()
