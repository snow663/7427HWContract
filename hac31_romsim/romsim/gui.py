from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from pathlib import Path

from .simulator import StopReason
from .workbench import SimulatorWorkbench, parse_number


APP_TITLE = "7427 $31 ROM Simulator"
MAX_VISIBLE_ROWS = 750
GUARD_FAILED = object()


def _hex(value: int, width: int = 4) -> str:
    return f"${value:0{width}X}"


def _dump(data: bytes, start: int) -> str:
    rows: list[str] = []
    for offset in range(0, len(data), 16):
        chunk = data[offset:offset + 16]
        address = (start + offset) & 0xFFFF
        hexes = " ".join(f"{value:02X}" for value in chunk)
        text = "".join(chr(value) if 32 <= value <= 126 else "." for value in chunk)
        rows.append(f"{address:04X}  {hexes:<47}  {text}")
    return "\n".join(rows)


class ROMSimulatorGUI:
    def __init__(self, root: tk.Tk, workbench: SimulatorWorkbench | None = None) -> None:
        self.root = root
        self.workbench = workbench or SimulatorWorkbench.default()
        self.sim = self.workbench.sim
        self.running = False
        self.run_batch = 1_000
        self.trace_cursor = 0
        self.bus_cursor = 0
        self.output_cursor = 0
        self._last_register_refresh = -1

        self.status_var = tk.StringVar(value="Load a BIN image to begin")
        self.image_var = tk.StringVar(value="No BIN loaded")
        self.run_state_var = tk.StringVar(value="STOPPED")
        self.cycle_budget_var = tk.StringVar(value="100")
        self.step_count_var = tk.StringVar(value="1")
        self.memory_address_var = tk.StringVar(value="$0000")
        self.memory_count_var = tk.StringVar(value="128")
        self.memory_value_var = tk.StringVar(value="$00")
        self.breakpoint_var = tk.StringVar(value="$7150")
        self.output_breakpoint_var = tk.StringVar(value="$3FCE")

        self.input_vars = {
            "state": tk.StringVar(value=self.sim.inputs.engine_state),
            "rpm": tk.StringVar(value=str(self.sim.inputs.rpm)),
            "map": tk.StringVar(value=str(self.sim.inputs.map_kpa)),
            "tps": tk.StringVar(value=str(self.sim.inputs.tps_pct)),
            "coolant": tk.StringVar(value=str(self.sim.inputs.coolant_c)),
            "battery": tk.StringVar(value=str(self.sim.inputs.battery_v)),
            "vss": tk.StringVar(value=str(self.sim.inputs.vss_mph)),
        }
        self.adc_vars = [tk.IntVar(value=value) for value in self.sim.inputs.adc]
        self.port_vars = {
            "port_a": tk.StringVar(value="$00"),
            "port_c": tk.StringVar(value="$00"),
            "port_e": tk.StringVar(value="$00"),
        }
        self.register_vars = {
            name: tk.StringVar(value="--")
            for name in ("PC", "SP", "A", "B", "D", "X", "Y", "CCR", "FLAGS", "CYC", "INS", "REG", "RAM")
        }

        self._configure_window()
        self._build_menu()
        self._build_toolbar()
        self._build_workspace()
        self._build_statusbar()
        self._bind_shortcuts()
        self._refresh_all(force=True)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _configure_window(self) -> None:
        self.root.title(APP_TITLE)
        self.root.geometry("1320x820")
        self.root.minsize(980, 640)
        self.root.rowconfigure(2, weight=1)
        self.root.columnconfigure(0, weight=1)
        style = ttk.Style(self.root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Run.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("State.TLabel", font=("Consolas", 10, "bold"))
        style.configure("PC.TLabel", font=("Consolas", 18, "bold"))

    def _build_menu(self) -> None:
        menu = tk.Menu(self.root)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Load BIN…", accelerator="Ctrl+O", command=self.load_bin)
        file_menu.add_command(label="Load scenario…", command=self.load_scenario)
        file_menu.add_command(label="Load HAC annotations…", command=self.load_hac)
        file_menu.add_separator()
        file_menu.add_command(label="Save trace…", accelerator="Ctrl+S", command=self.save_trace)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.close)
        menu.add_cascade(label="File", menu=file_menu)

        sim_menu = tk.Menu(menu, tearoff=False)
        sim_menu.add_command(label="Run / pause", accelerator="F5", command=self.toggle_run)
        sim_menu.add_command(label="Step instruction", accelerator="F10", command=self.step_instructions)
        sim_menu.add_command(label="Step cycle budget", accelerator="F11", command=self.step_cycles)
        sim_menu.add_command(label="Reset", accelerator="Ctrl+R", command=self.reset)
        menu.add_cascade(label="Simulation", menu=sim_menu)

        help_menu = tk.Menu(menu, tearoff=False)
        help_menu.add_command(label="About", command=self.show_about)
        menu.add_cascade(label="Help", menu=help_menu)
        self.root.configure(menu=menu)

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self.root, padding=(8, 7))
        bar.grid(row=0, column=0, sticky="ew")
        bar.columnconfigure(11, weight=1)
        ttk.Button(bar, text="Load BIN…", command=self.load_bin).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(bar, text="Reset", command=self.reset).grid(row=0, column=1, padx=5)
        self.run_button = ttk.Button(bar, text="▶ Run", style="Run.TButton", command=self.toggle_run)
        self.run_button.grid(row=0, column=2, padx=(12, 5))
        ttk.Button(bar, text="❚❚ Pause", command=self.pause).grid(row=0, column=3, padx=5)
        ttk.Separator(bar, orient="vertical").grid(row=0, column=4, sticky="ns", padx=8)
        ttk.Label(bar, text="Instructions").grid(row=0, column=5, padx=(0, 3))
        ttk.Entry(bar, textvariable=self.step_count_var, width=7).grid(row=0, column=6)
        ttk.Button(bar, text="Step", command=self.step_instructions).grid(row=0, column=7, padx=(3, 10))
        ttk.Label(bar, text="E-cycles").grid(row=0, column=8, padx=(0, 3))
        ttk.Entry(bar, textvariable=self.cycle_budget_var, width=9).grid(row=0, column=9)
        ttk.Button(bar, text="Advance", command=self.step_cycles).grid(row=0, column=10, padx=(3, 10))
        ttk.Label(bar, textvariable=self.run_state_var, style="State.TLabel").grid(row=0, column=12, padx=(10, 0))

        identity = ttk.Frame(self.root, padding=(10, 0, 10, 6))
        identity.grid(row=1, column=0, sticky="ew")
        identity.columnconfigure(0, weight=1)
        ttk.Label(identity, textvariable=self.image_var).grid(row=0, column=0, sticky="w")

    def _build_workspace(self) -> None:
        split = ttk.Panedwindow(self.root, orient="horizontal")
        split.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 7))

        controls = ttk.Frame(split, width=320)
        controls.rowconfigure(0, weight=1)
        controls.columnconfigure(0, weight=1)
        split.add(controls, weight=0)
        control_tabs = ttk.Notebook(controls)
        control_tabs.grid(row=0, column=0, sticky="nsew")
        self._build_input_tab(control_tabs)
        self._build_raw_tab(control_tabs)
        self._build_control_tab(control_tabs)

        display = ttk.Frame(split)
        display.rowconfigure(0, weight=1)
        display.columnconfigure(0, weight=1)
        split.add(display, weight=1)
        self.display_tabs = ttk.Notebook(display)
        self.display_tabs.grid(row=0, column=0, sticky="nsew")
        self._build_cpu_tab(self.display_tabs)
        self._build_trace_tab(self.display_tabs)
        self._build_bus_tab(self.display_tabs)
        self._build_output_tab(self.display_tabs)
        self._build_memory_tab(self.display_tabs)

    def _build_input_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=10)
        tab.columnconfigure(1, weight=1)
        notebook.add(tab, text="Engine inputs")
        fields = [
            ("Engine state", "state", ""),
            ("RPM", "rpm", "rpm"),
            ("MAP", "map", "kPa"),
            ("TPS", "tps", "%"),
            ("Coolant", "coolant", "°C"),
            ("Battery", "battery", "V"),
            ("Vehicle speed", "vss", "mph"),
        ]
        for row, (label, key, unit) in enumerate(fields):
            ttk.Label(tab, text=label).grid(row=row, column=0, sticky="w", pady=4)
            if key == "state":
                widget = ttk.Combobox(tab, textvariable=self.input_vars[key], values=("KEY_ON", "CRANK", "RUN", "DECEL", "STALL"))
            else:
                widget = ttk.Entry(tab, textvariable=self.input_vars[key])
            widget.grid(row=row, column=1, sticky="ew", padx=(8, 4), pady=4)
            ttk.Label(tab, text=unit).grid(row=row, column=2, sticky="w", pady=4)
        ttk.Button(tab, text="Apply engine inputs", command=self.apply_engine_inputs).grid(
            row=len(fields), column=0, columnspan=3, sticky="ew", pady=(12, 6)
        )
        ttk.Separator(tab).grid(row=len(fields) + 1, column=0, columnspan=3, sticky="ew", pady=8)
        ttk.Label(
            tab,
            text="MAP, TPS, coolant, battery and VSS are trace metadata until their ADC or hardware bindings are proven.",
            wraplength=275,
            justify="left",
        ).grid(row=len(fields) + 2, column=0, columnspan=3, sticky="w")

    def _build_raw_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=8)
        tab.columnconfigure(1, weight=1)
        notebook.add(tab, text="Raw ADC / I/O")
        for channel, variable in enumerate(self.adc_vars):
            ttk.Label(tab, text=f"ADC {channel}").grid(row=channel, column=0, sticky="w")
            scale = tk.Scale(
                tab, from_=0, to=255, orient="horizontal", variable=variable,
                showvalue=True, resolution=1, length=205, highlightthickness=0,
            )
            scale.grid(row=channel, column=1, columnspan=2, sticky="ew", padx=(5, 0))
        base_row = len(self.adc_vars)
        for offset, (key, label) in enumerate((("port_a", "PORT A"), ("port_c", "PORT C"), ("port_e", "PORT E"))):
            row = base_row + offset
            ttk.Label(tab, text=label).grid(row=row, column=0, sticky="w", pady=3)
            ttk.Entry(tab, textvariable=self.port_vars[key], width=10).grid(row=row, column=1, sticky="ew", padx=5, pady=3)
        ttk.Button(tab, text="Apply raw ADC and ports", command=self.apply_raw_inputs).grid(
            row=base_row + 3, column=0, columnspan=3, sticky="ew", pady=(10, 4)
        )

    def _build_control_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=10)
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        notebook.add(tab, text="Break / IRQ")
        ttk.Label(tab, text="PC breakpoint").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Entry(tab, textvariable=self.breakpoint_var).grid(row=1, column=0, sticky="ew", pady=(2, 5))
        ttk.Button(tab, text="Toggle", command=self.toggle_pc_breakpoint).grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(2, 5))
        ttk.Label(tab, text="Output breakpoint").grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Entry(tab, textvariable=self.output_breakpoint_var).grid(row=3, column=0, sticky="ew", pady=(2, 5))
        ttk.Button(tab, text="Toggle", command=self.toggle_output_breakpoint).grid(row=3, column=1, sticky="ew", padx=(5, 0), pady=(2, 5))
        self.breakpoint_list = tk.Listbox(tab, height=8, font=("Consolas", 9))
        self.breakpoint_list.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(8, 12))

        ttk.Label(tab, text="Request interrupt").grid(row=5, column=0, columnspan=2, sticky="w", pady=(4, 4))
        interrupts = ("IRQ", "XIRQ", "TOC1", "TOC2", "TOC3", "TOC4", "TOC5")
        for index, name in enumerate(interrupts):
            ttk.Button(tab, text=name, command=lambda value=name: self.request_interrupt(value)).grid(
                row=6 + index // 2, column=index % 2, sticky="ew", padx=(0 if index % 2 == 0 else 3, 3 if index % 2 == 0 else 0), pady=3
            )

    def _build_cpu_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=8)
        tab.rowconfigure(2, weight=1)
        tab.columnconfigure(0, weight=1)
        notebook.add(tab, text="CPU / mapped registers")

        head = ttk.Frame(tab)
        head.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(head, textvariable=self.register_vars["PC"], style="PC.TLabel").grid(row=0, column=0, rowspan=2, padx=(0, 20))
        fields = ("SP", "A", "B", "D", "X", "Y", "CCR", "FLAGS")
        for column, name in enumerate(fields, start=1):
            ttk.Label(head, text=name).grid(row=0, column=column, padx=7)
            ttk.Label(head, textvariable=self.register_vars[name], style="State.TLabel").grid(row=1, column=column, padx=7)

        timing = ttk.Frame(tab)
        timing.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        for column, name in enumerate(("CYC", "INS", "REG", "RAM")):
            ttk.Label(timing, text=f"{name}: ").grid(row=0, column=column * 2, sticky="e")
            ttk.Label(timing, textvariable=self.register_vars[name], style="State.TLabel").grid(row=0, column=column * 2 + 1, sticky="w", padx=(0, 16))

        columns = ("address", "value", "name", "access", "evidence")
        self.register_tree = self._tree(tab, columns, (75, 80, 310, 70, 125), row=2)

    def _build_trace_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=6)
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)
        notebook.add(tab, text="Execution")
        columns = ("cycle", "pc", "opcode", "instruction")
        self.trace_tree = self._tree(tab, columns, (105, 75, 75, 580), row=0)

    def _build_bus_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=6)
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)
        notebook.add(tab, text="Memory bus")
        columns = ("cycle", "pc", "rw", "address", "value", "device", "symbol", "evidence")
        self.bus_tree = self._tree(tab, columns, (95, 70, 42, 75, 60, 145, 245, 120), row=0)

    def _build_output_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=6)
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)
        notebook.add(tab, text="Outputs")
        columns = ("cycle", "pc", "address", "value", "name", "subsystem", "evidence")
        self.output_tree = self._tree(tab, columns, (95, 70, 75, 85, 315, 160, 120), row=0)

    def _build_memory_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=8)
        tab.rowconfigure(1, weight=1)
        tab.columnconfigure(0, weight=1)
        notebook.add(tab, text="Memory inspector")
        controls = ttk.Frame(tab)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 7))
        ttk.Label(controls, text="Address").grid(row=0, column=0)
        ttk.Entry(controls, textvariable=self.memory_address_var, width=12).grid(row=0, column=1, padx=(3, 8))
        ttk.Label(controls, text="Bytes").grid(row=0, column=2)
        ttk.Entry(controls, textvariable=self.memory_count_var, width=8).grid(row=0, column=3, padx=(3, 8))
        ttk.Button(controls, text="Refresh", command=self.refresh_memory).grid(row=0, column=4, padx=(0, 16))
        ttk.Label(controls, text="Value").grid(row=0, column=5)
        ttk.Entry(controls, textvariable=self.memory_value_var, width=9).grid(row=0, column=6, padx=(3, 6))
        ttk.Button(controls, text="Write RAM / I/O", command=self.write_memory).grid(row=0, column=7, padx=3)
        ttk.Button(controls, text="Patch ROM…", command=self.patch_rom).grid(row=0, column=8, padx=3)
        self.memory_text = tk.Text(tab, wrap="none", font=("Consolas", 10), state="disabled")
        self.memory_text.grid(row=1, column=0, sticky="nsew")
        yscroll = ttk.Scrollbar(tab, orient="vertical", command=self.memory_text.yview)
        yscroll.grid(row=1, column=1, sticky="ns")
        self.memory_text.configure(yscrollcommand=yscroll.set)

    def _tree(self, parent: ttk.Frame, columns: tuple[str, ...], widths: tuple[int, ...], row: int) -> ttk.Treeview:
        holder = ttk.Frame(parent)
        holder.grid(row=row, column=0, sticky="nsew")
        holder.rowconfigure(0, weight=1)
        holder.columnconfigure(0, weight=1)
        tree = ttk.Treeview(holder, columns=columns, show="headings", selectmode="browse")
        for name, width in zip(columns, widths):
            tree.heading(name, text=name.replace("_", " ").title())
            tree.column(name, width=width, minwidth=45, stretch=name in {"name", "instruction", "symbol"})
        tree.grid(row=0, column=0, sticky="nsew")
        yscroll = ttk.Scrollbar(holder, orient="vertical", command=tree.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll = ttk.Scrollbar(holder, orient="horizontal", command=tree.xview)
        xscroll.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        return tree

    def _build_statusbar(self) -> None:
        bar = ttk.Frame(self.root, padding=(8, 3))
        bar.grid(row=3, column=0, sticky="ew")
        bar.columnconfigure(0, weight=1)
        ttk.Label(bar, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        ttk.Label(bar, text="Instruction-atomic timing", style="State.TLabel").grid(row=0, column=1, sticky="e")

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Control-o>", lambda _event: self.load_bin())
        self.root.bind("<Control-s>", lambda _event: self.save_trace())
        self.root.bind("<Control-r>", lambda _event: self.reset())
        self.root.bind("<F5>", lambda _event: self.toggle_run())
        self.root.bind("<F10>", lambda _event: self.step_instructions())
        self.root.bind("<F11>", lambda _event: self.step_cycles())

    def _guard(self, action, *, pause: bool = True):
        try:
            if pause:
                self.pause()
            result = action()
            self._refresh_all(force=True)
            return result
        except Exception as exc:
            self.running = False
            self._set_running_display()
            messagebox.showerror(APP_TITLE, str(exc), parent=self.root)
            self.status_var.set(f"Error: {exc}")
            return GUARD_FAILED

    def load_bin(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Load PCM BIN",
            filetypes=(("PCM binary", "*.bin *.BIN"), ("All files", "*.*")),
        )
        if not path:
            return

        def action() -> None:
            try:
                self.workbench.load_bin(path)
            except ValueError as exc:
                if "cannot infer load base" not in str(exc):
                    raise
                base = simpledialog.askstring(
                    APP_TITLE,
                    "This image size has no unambiguous load base. Enter the CPU address, such as $4000:",
                    parent=self.root,
                )
                if base is None:
                    return
                self.workbench.load_bin(path, base)
            self._reset_view_cursors()
            self.status_var.set(f"Loaded {Path(path).name} and reset from vector $FFFE")

        self._guard(action)

    def load_scenario(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root, title="Load simulation scenario", filetypes=(("JSON scenario", "*.json"), ("All files", "*.*"))
        )
        if path:
            if self._guard(lambda: self.sim.load_scenario(path)) is not GUARD_FAILED:
                self.status_var.set(f"Scenario loaded: {Path(path).name}")

    def load_hac(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root, title="Load optional HAC annotations", filetypes=(("HTML", "*.html *.htm"), ("All files", "*.*"))
        )
        if not path:
            return

        def action() -> None:
            count = self.sim.load_hac_symbols(path)
            self.status_var.set(f"Loaded {count} optional HAC hint lines; hints are not contract facts")

        self._guard(action, pause=False)

    def save_trace(self) -> None:
        if not self.workbench.image_loaded:
            messagebox.showinfo(APP_TITLE, "Load and run a BIN before saving a trace.", parent=self.root)
            return
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save chronological trace",
            defaultextension=".jsonl",
            filetypes=(("JSON Lines", "*.jsonl"), ("All files", "*.*")),
        )
        if path:
            if self._guard(lambda: self.sim.trace.write_jsonl(path), pause=False) is not GUARD_FAILED:
                self.status_var.set(f"Trace saved: {path}")

    def reset(self) -> None:
        if not self.workbench.image_loaded:
            self.status_var.set("Load a BIN image to begin")
            return

        def action() -> None:
            self.workbench.reset()
            self._reset_view_cursors()
            self.status_var.set("PCM reset complete")

        self._guard(action)

    def toggle_run(self) -> None:
        if self.running:
            self.pause()
            return
        if not self.workbench.image_loaded:
            self.load_bin()
            if not self.workbench.image_loaded:
                return
        self.running = True
        self._set_running_display()
        self.status_var.set("Running continuously; Pause or F5 stops after the current instruction batch")
        self.root.after(1, self._run_once)

    def pause(self) -> None:
        self.running = False
        self._set_running_display()

    def _run_once(self) -> None:
        if not self.running:
            self._refresh_all(force=True)
            return
        try:
            result = self.workbench.run_chunk(self.run_batch)
        except Exception as exc:
            self.running = False
            self._set_running_display()
            messagebox.showerror(APP_TITLE, str(exc), parent=self.root)
            return
        self._refresh_all()
        if result.reason != StopReason.LIMIT:
            self.running = False
            self._set_running_display()
            self.status_var.set(f"Stopped: {result.reason.value} {result.detail}".strip())
            self._refresh_all(force=True)
            return
        self.root.after(1, self._run_once)

    def step_instructions(self) -> None:
        def action() -> None:
            count = max(1, parse_number(self.step_count_var.get()))
            elapsed = self.workbench.step_instructions(count)
            self.status_var.set(f"Executed {count} instruction(s), advancing {elapsed} E-cycles")

        self._guard(action)

    def step_cycles(self) -> None:
        def action() -> None:
            budget = max(1, parse_number(self.cycle_budget_var.get()))
            result = self.workbench.step_cycles(budget)
            self.status_var.set(
                f"Cycle budget {budget}: advanced {result.cycles} E-cycles in {result.instructions} instruction(s)"
            )

        self._guard(action)

    def apply_engine_inputs(self) -> None:
        values = {name: variable.get() for name, variable in self.input_vars.items()}
        if self._guard(lambda: self.workbench.apply_inputs(values), pause=False) is not GUARD_FAILED:
            self.status_var.set("Engine input state applied")

    def apply_raw_inputs(self) -> None:
        def action() -> None:
            values: dict[str, str | int] = {
                f"adc.{index}": variable.get() for index, variable in enumerate(self.adc_vars)
            }
            values.update({name: parse_number(variable.get()) for name, variable in self.port_vars.items()})
            self.workbench.apply_inputs(values)

        if self._guard(action, pause=False) is not GUARD_FAILED:
            self.status_var.set("Raw ADC and port state applied")

    def toggle_pc_breakpoint(self) -> None:
        result = self._guard(lambda: self.workbench.toggle_breakpoint(self.breakpoint_var.get()), pause=False)
        if result is not GUARD_FAILED:
            self.status_var.set("PC breakpoint added" if result else "PC breakpoint removed")

    def toggle_output_breakpoint(self) -> None:
        result = self._guard(
            lambda: self.workbench.toggle_breakpoint(self.output_breakpoint_var.get(), output=True), pause=False
        )
        if result is not GUARD_FAILED:
            self.status_var.set("Output breakpoint added" if result else "Output breakpoint removed")

    def request_interrupt(self, vector: str) -> None:
        if self._guard(lambda: self.workbench.request_interrupt(vector), pause=False) is not GUARD_FAILED:
            self.status_var.set(f"Queued {vector} interrupt")

    def refresh_memory(self) -> None:
        def action() -> None:
            address = parse_number(self.memory_address_var.get()) & 0xFFFF
            count = min(4096, max(1, parse_number(self.memory_count_var.get())))
            data = self.workbench.read_memory(address, count)
            self.memory_text.configure(state="normal")
            self.memory_text.delete("1.0", "end")
            self.memory_text.insert("1.0", _dump(data, address))
            self.memory_text.configure(state="disabled")
            self.status_var.set(f"Read {count} byte(s) from {_hex(address)}")

        self._guard(action, pause=False)

    def write_memory(self) -> None:
        def action() -> None:
            address = parse_number(self.memory_address_var.get()) & 0xFFFF
            value = parse_number(self.memory_value_var.get()) & 0xFF
            self.workbench.write_memory(address, value)
            self.status_var.set(f"Wrote {_hex(value, 2)} to {_hex(address)}")
            self.refresh_memory()

        self._guard(action)

    def patch_rom(self) -> None:
        try:
            address = parse_number(self.memory_address_var.get()) & 0xFFFF
            value = parse_number(self.memory_value_var.get()) & 0xFF
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc), parent=self.root)
            return
        if not messagebox.askyesno(
            APP_TITLE,
            f"Patch ROM byte {_hex(address)} to {_hex(value, 2)} for this simulator session?\n\nThe BIN file on disk is not modified.",
            parent=self.root,
        ):
            return
        self._guard(lambda: self.workbench.write_memory(address, value, patch_rom=True))
        self.status_var.set(f"Session ROM patch: {_hex(address)} = {_hex(value, 2)}")
        self.refresh_memory()

    def _reset_view_cursors(self) -> None:
        self.trace_cursor = 0
        self.bus_cursor = 0
        self.output_cursor = 0
        for tree in (getattr(self, "trace_tree", None), getattr(self, "bus_tree", None), getattr(self, "output_tree", None)):
            if tree is not None:
                tree.delete(*tree.get_children())

    def _refresh_all(self, force: bool = False) -> None:
        self._refresh_identity()
        self._refresh_cpu()
        self._refresh_breakpoints()
        self._refresh_trace_trees()
        cycle = self.sim.memory.cycle_counter
        if force or cycle - self._last_register_refresh >= 2_000:
            self._refresh_mapped_registers()
            self._last_register_refresh = cycle

    def _refresh_identity(self) -> None:
        if not self.workbench.image_loaded:
            self.image_var.set("No BIN loaded")
            return
        path = Path(self.sim.bin_path or "")
        digest = self.sim.bin_sha256 or ""
        base = _hex(self.sim.bin_base or 0)
        self.image_var.set(f"{path.name}   base {base}   {self.sim.image_identity}   SHA-256 {digest[:16]}…")

    def _refresh_cpu(self) -> None:
        state = self.sim.cpu.s
        flags = "".join(letter if state.ccr & mask else "." for letter, mask in zip("SXHINZVC", (0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01)))
        values = {
            "PC": _hex(state.pc), "SP": _hex(state.sp), "A": _hex(state.a, 2), "B": _hex(state.b, 2),
            "D": _hex(state.d), "X": _hex(state.x), "Y": _hex(state.y), "CCR": _hex(state.ccr, 2),
            "FLAGS": flags, "CYC": str(self.sim.memory.cycle_counter), "INS": str(self.sim.instruction_counter),
            "REG": _hex(self.sim.memory.reg_base), "RAM": _hex(self.sim.memory.ram_base),
        }
        for name, value in values.items():
            self.register_vars[name].set(value)

    def _refresh_breakpoints(self) -> None:
        rows = [f"PC      {_hex(value)}" for value in sorted(self.sim.breakpoints)]
        rows += [f"OUTPUT  {_hex(value)}" for value in sorted(self.sim.output_breakpoints)]
        existing = list(self.breakpoint_list.get(0, "end"))
        if rows != existing:
            self.breakpoint_list.delete(0, "end")
            for row in rows:
                self.breakpoint_list.insert("end", row)

    def _refresh_trace_trees(self) -> None:
        traces = self.sim.cpu.exec_trace
        if self.trace_cursor > len(traces):
            self.trace_tree.delete(*self.trace_tree.get_children())
            self.trace_cursor = 0
        for row in traces[self.trace_cursor:]:
            prefix = f"{row.prefix:02X} " if row.prefix is not None else ""
            label = self.sim.symbols.label(row.pc)
            instruction = f"{row.text}{'  [' + label + ':hac_hint]' if label else ''}"
            self.trace_tree.insert("", "end", values=(row.cycle, _hex(row.pc), f"{prefix}{row.opcode:02X}", instruction))
        self.trace_cursor = len(traces)

        accesses = self.sim.trace.accesses
        if self.bus_cursor > len(accesses):
            self.bus_tree.delete(*self.bus_tree.get_children())
            self.bus_cursor = 0
        for row in accesses[self.bus_cursor:]:
            self.bus_tree.insert("", "end", values=(
                row.cycle, _hex(row.pc), row.access_type, _hex(row.address), _hex(row.value, 2),
                row.device, row.symbol, row.evidence,
            ))
        self.bus_cursor = len(accesses)

        outputs = self.sim.trace.outputs
        if self.output_cursor > len(outputs):
            self.output_tree.delete(*self.output_tree.get_children())
            self.output_cursor = 0
        for row in outputs[self.output_cursor:]:
            width = 4 if row.width == 16 else 2
            self.output_tree.insert("", "end", values=(
                row.cycle, _hex(row.pc), _hex(row.address), _hex(row.value, width),
                row.name, row.subsystem, row.evidence,
            ))
        self.output_cursor = len(outputs)

        for tree in (self.trace_tree, self.bus_tree, self.output_tree):
            children = tree.get_children()
            excess = len(children) - MAX_VISIBLE_ROWS
            if excess > 0:
                tree.delete(*children[:excess])
            if children:
                tree.yview_moveto(1.0)

    def _refresh_mapped_registers(self) -> None:
        self.register_tree.delete(*self.register_tree.get_children())
        memory = self.sim.memory
        for address, contract in sorted(self.sim.profile.registers.items()):
            if contract.width == 16:
                value = (memory.debug_read8(address) << 8) | memory.debug_read8((address + 1) & 0xFFFF)
                shown = _hex(value, 4)
            else:
                shown = _hex(memory.debug_read8(address), 2)
            self.register_tree.insert("", "end", values=(
                _hex(address), shown, contract.name, contract.access, contract.evidence.value,
            ))

    def _set_running_display(self) -> None:
        if self.running:
            self.run_state_var.set("RUNNING")
            self.run_button.configure(text="❚❚ Pause")
        else:
            self.run_state_var.set("STOPPED")
            self.run_button.configure(text="▶ Run")

    def show_about(self) -> None:
        messagebox.showinfo(
            APP_TITLE,
            "Contract-driven MC68HC11 / GM 16197427 $31 ROM simulator.\n\n"
            "Repository contracts outrank HAC annotations. Green lights in software are not bench proof.\n\n"
            "Current timing is instruction-atomic; true E-cycle micro-operation stepping is a planned fidelity gate.",
            parent=self.root,
        )

    def close(self) -> None:
        self.running = False
        self.sim.trace.close_stream()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    ROMSimulatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
