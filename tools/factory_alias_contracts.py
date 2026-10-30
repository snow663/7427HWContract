"""Reviewed address formulas supplementing the finite-set ROM pointer analysis.

These are documentation contracts, not emulator overrides. A finite footprint
is conditional on its stated entry/state invariant. Runtime supplied pointers
remain expressions; no target whitelist is manufactured for them.
"""
from __future__ import annotations


def contracts(rom, instructions):
    result = {}

    def add(pcs, base, role, proof, targets=None, guard="resident normal-return path", kind="address_formula"):
        for raw in pcs.split():
            pc = int(raw, 16)
            if pc in result:
                raise ValueError(f"Duplicate reviewed alias {pc:04X}")
            i = instructions[pc]
            if not i.mode.startswith("indexed_"):
                raise ValueError(f"Alias is not an indexed instruction: {pc:04X}")
            addresses = None if targets is None else sorted({(x+i.value)&65535 for x in targets})
            result[pc] = dict(base_expression=base,
                              effective_address=f"u16(({base}) + ${i.value:02X})",
                              role=role, proof_pcs=proof, condition=guard, kind=kind,
                              addresses=addresses)

    def seq(start, end):
        return range(start, end)

    add("7182", "serial_clear_cursor", "boot serial clear", "717F-7188",
        seq(0x0360, 0x03FF), "X starts 0360; increments until X=03FF; 03FF excluded")
    add("724A", "032B-j", "retained transmission checksum scan", "723F-7256",
        seq(0x02F8, 0x032C), "j=0..51; no interrupted mutation of checksum/cursor")
    add("7263", "02F8+j", "retained transmission checksum rejection fill", "7257-7268",
        seq(0x02F8, 0x032C), "validation rejected; 52 incrementing stores")
    refresh = "7484 7486 7488 748A 748C 748E 7490 7492 7494 7496 7498 749A 749C 749E 74A0 74A2"
    add(refresh, "refresh_block_cursor", "interrupt-masked self-copy; preserves stored bits", "7470-74B0",
        list(range(0,0x400,16))+list(range(0x800,0x900,16)),
        "029B initially zero; only resident cursor updates; 0400 redirects to 0800; 0900 terminates")
    add("74B7", "03B0+j", "stack watermark scan", "74B4-74C3",
        seq(0x03B0,0x0400), "j=0..79; stop on nonzero or X>=03FF")
    add("7501", "465D+((byte[0062]>>1)&FE)", "reference timer delay word", "74F1-7503",
        range(0x465D,0x46DC,2))
    add("784C", "crank_gain_base+crank_index", "crank event gain", "7827-784C",
        list(range(0x4DDE,0x4E26))+list(range(0x4E26,0x4E2E)),
        "index=count02CE for count<=23; otherwise count&7; bases4DDE/4DF6/4E0E or4E26")
    add("8D7D", "02B3+selected_BLM_index", "BLM selection read", "8D2B-8D9B",
        range(0x02B3,0x02C8), "selected index0..20; stock cell state; external mutations excluded")
    add("8E78 8E9A", "02B3+byte[0247]", "BLM learn read/write", "8D9B;8E50-8E9A",
        range(0x02B3,0x02C8), "0247 was produced by resident selector0..20")
    add("97C8", "SP_at_97C6-1", "locally saved X word", "97C6-97CA", kind="local_frame")
    add("9878", "SP_at_986D-1", "saved final IAC flow word", "986C-987A", kind="local_frame")
    add("9891 9897", "4E92+hi(u16((flow088B>>4)+((flow088B>>3)&1)))",
        "IAC increasing-table position conversion", "9880-9899", range(0x4E92,0x4EA3))
    add("99BA 99BE", "504D+(byte[0036]&03)", "IAC stall threshold", "99AD-99C1", range(0x504D,0x5051))
    add("9A80", "5051+(byte[0036]&03)", "IAC mode parameter", "9A77-9A82", range(0x5051,0x5055))
    add("AD29 AD54 AD58", "5113+j", "VSS ratio classifier", "ACE3;AD12-AD36",
        range(0x5113,0x5117), "X saved across divisions; j=0..3; failed test increments X and 0845")
    add("B2C6", "selected_speed_pointer_table+u8(2*gear_or_forced_one)",
        "speed estimator word pointer selection", "B2B2-B2C8",
        guard="table supplied by caller; 0098.2 substitutes gear=1 before byte ASLB")
    add("B30E B313", "B31D+byte[0152]", "transmission temperature gain bytes", "B2ED-B318",
        range(0xB31D,0xB325), "0152 boot zero then resident temperature classifier0..7")
    add("B417 B433", "68A9+2*u8(byte[00D9]-1)", "shift ratio bounds", "B3E0-B417",
        [0x68A9,0x68AB,0x68AD], "normal upshift, gear1..3; both ABX use the same byte")
    add("B42F", "0189+u8(byte[00D9]-1)", "shift origin snapshot", "B428-B42F",
        [0x0189,0x018A,0x018B], "normal upshift gear1..3")
    add("B47F", "019C+u8(byte[00D9]-1)", "mean ratio snapshot", "B478-B47F",
        [0x019C,0x019D,0x019E], "normal upshift gear1..3")
    add("B48A", "68CB+u8(byte[00D9]-1)", "short observation threshold", "B481-B48A",
        [0x68CB,0x68CC,0x68CD], "normal upshift gear1..3")
    add("B4A4", "68B5+byte[00D9]", "other shift completion threshold", "B49C-B4A4", range(0x68B5,0x68B9))
    add("B4CC B4D5 B4DD B4E1 B53D B545 B553", "68B8+u8(byte[00D9]-1)",
        "per-gear learning qualifications", "B4B4-B4BA;B529-B539",
        [0x68B8,0x68B9,0x68BA,0x69B7],
        "D9=0..3; D9=0 byte decrement gives FF, then unsigned indexed displacement")
    add("B5BB", "0115+pressure_shift_index", "pressure shift override", "B5AC-B5BB",
        guard="index=u8(D9-1), plus1 for downshift snapshot83.4; BMI excludes indices128..255")
    add("B5D0", "B96D+u8(2*(pressure_shift_index+pattern_offset))",
        "pressure shift curve pointer", "B5AC-B5D0",
        guard="pattern_offset=0,3,6 from9F bits06; shifted index is byte-wrapped")
    add("B5F9", "B991+u8(2*byte[00D9])", "pressure temperature curve pointer", "B5F2-B5F9",
        [0xB991,0xB993,0xB995,0xB997])
    add("B620 B631", "5F29+j", "TPS pressure interpolation upper knot", "B60D-B637",
        [0x5F29,0x5F2A,0x5F2B], "TPS strictly between ROM5F28 and5F2B; ascending stock knots; j0..2")
    add("B634 B64A", "5F28+j", "TPS pressure interpolation lower cursor", "B631-B64A",
        [0x5F28,0x5F29,0x5F2A], "DEX after upper-knot read; stock ascending knot domain")
    add("B6A6", "B97F+u8(2*(byte[00D9]+pattern_offset))",
        "pressure alternate curve pointer", "B68F-B6A6")
    add("B6CD", "B999+u8(2*pressure_shift_index)", "pressure shift curve pointer", "B6BD-B6CD")
    add("B845", "5F21+byte[00D9]", "pressure speed subtractor", "B83F-B845", range(0x5F21,0x5F25))
    add("B8B6", "5F16+u8(byte[00D9]-1)", "shift pressure adder", "B8AD-B8B6",
        [0x5F16,0x5F17,0x5F18], "BMI excludes gear0 decrement; resident gear1..3")
    add("B93F", "BC65+u8(2*u8(adaptive_gear_context-1))", "adaptive bank pointer", "B91D-B93F",
        [0xBC65,0xBC67,0xBC69], "context derived fromD9 and83 snapshots; BMI excludes zero gear")
    add("B9C1 BA0A", "BC65+2*byte[014A]", "adaptive reset destination bank pointer", "B9AB-B9C1;B9FA-BA0A",
        [0xBC65,0xBC67,0xBC69], "bank loop014A=0..2")
    add("B9C3", "BA32+2*byte[014A]", "adaptive restore source pointer", "B9AB-B9C3",
        [0xBA32,0xBA34,0xBA36], "bank loop014A=0..2")
    add("B9D3 B9D9 BA1B BA20", "word[BC65+2*bank]+j", "adaptive bank reset read/write", "B9C6-B9E4;BA0C-BA2A",
        range(0x02F8,0x032B), "bank0..2; j0..16; per-byte checksum update under SEI/CLI")
    add("B9D5", "word[BA32+2*bank]+j", "adaptive restore calibration source", "B9C3-B9E4",
        range(0x6A81,0x6AB4), "bank0..2; j0..16")
    add("BA48", "BA5F+u8(2*u8(byte[00D9]-1))", "adaptive event-counter bank pointer", "BA40-BA48",
        [0xBA5F,0xBA61,0xBA63,0xBB5D], "resident gear0..3; gear0 wraps byte ASLB toFE; zero-event admission is separate")
    add("BA50", "selected_counter_bank+byte[0149]", "adaptive event counter", "BA48-BA50",
        list(range(0x032C,0x034E)), "nonzero pointer fromBA5F; active adaptive gear1..3; index0149=0..16")
    add("BAA0", "desired_time_pointer_table+u8(2*u8(byte[00D9]-1))", "desired shift-time curve pointer",
        "BA65-BAA0", guard="table=BC41/BC47/BC4D/BC53; normal completed upshift gear1..3")
    add("BAB4 BAC1", "0136+u8(byte[00D9]-1)", "measured time and signed error snapshots", "BAA7-BAC1",
        [0x0136,0x0137,0x0138], "normal completed upshift gear1..3")
    add("BAD4", "BC59+u8(2*u8(byte[00D9]-1))", "short-mean threshold curve pointer", "BACC-BAD4",
        [0xBC59,0xBC5B,0xBC5D], "normal completed upshift gear1..3")
    add("BAE2", "019C+u8(byte[00D9]-1)", "mean snapshot read", "BADB-BAE2",
        [0x019C,0x019D,0x019E], "normal completed upshift gear1..3")
    add("BAF5 BB09 BB1E BB24 BB2B", "699F+u8(byte[00D9]-1)", "adaptive step thresholds", "BAEE-BB2B",
        [0x699F,0x69A0,0x69A1], "normal completed upshift gear1..3")
    add("BB3A", "BC3B+u8(2*u8(byte[00D9]-1))", "signed-error step pointer", "BB32-BB3A",
        [0xBC3B,0xBC3D,0xBC3F], "normal completed upshift gear1..3")
    add("BB4B", "selected_step_table+clamped_error_index", "adaptive error step byte", "BB3A-BB4B",
        guard="clamped_error_index from DD+8 with signed BGE then unsigned cap16; see transmission contract")
    add("BB6F BC34", "BC65+u8(2*u8(byte[00D9]-1))", "active adaptive bank pointer", "BB65-BB6F;BC31-BC37",
        [0xBC65,0xBC67,0xBC69], "normal completed upshift gear1..3")
    add("BB93 BBEB BC21 BC2B", "word[BC65+2*(gear-1)]+neighbor", "adaptive neighbor read/commit", "BB76-BC37",
        range(0x02F8,0x032B), "gear1..3; j014B0..4; neighbor=u8(j+0149)-2 admitted only0..16")
    add("BBA5", "6A16+byte[014B]", "adaptive neighbor gain", "BB76-BBA5", range(0x6A16,0x6A1B), "j0..4")
    add("BBF8 BC07", "BC65+2*(gear-1)", "adaptive upper/lower curve pointer", "BB65-BB6F;BBF6-BC15",
        [0xBC65,0xBC67,0xBC69], "gear1..3; offsets0C/06 select parallel BC71/BC6B arrays")
    add("BD05", "5F2D+u8(byte[00D9]-1)", "shift pressure-origin elapsed bound", "BCFA-BD05",
        [0x5F2D,0x5F2E,0x5F2F], "resident gear1..3; BMI excludes0")
    add("BD12", "5F19+2*u8(byte[00D9]-1)", "low-gear ratio word", "BD09-BD12", [0x5F19,0x5F1B], "index0..1")
    add("BD2B", "BE55+2*u8(byte[00D9]-1)", "low-gear pressure curve pointer", "BD09-BD2B", [0xBE55,0xBE57], "index0..1")
    add("BD43", "BE37+u8(2*u8(byte[00D9]-1))", "pressure recovery ratio curve pointer", "BD3B-BD43",
        [0xBE37,0xBE39], "low-gear path gear1..2")
    add("BD58", "5F1D+u8(2*u8(byte[00D9]-1))", "pressure recovery ratio word", "BD41;BD54-BD58",
        [0x5F1D,0x5F1F], "low-gear path gear1..2; F4C1 preserves B")
    add("BD65", "BE49+u8(2*u8(byte[00D9]-1))", "pressure recovery age curve pointer", "BD61-BD65",
        [0xBE49,0xBE4B], "low-gear path gear1..2")
    add("BDFB", "pressure_recovery_table+recovery_word_offset", "pressure recovery offset curve pointer", "BD4E-BE00",
        [0xBE3D,0xBE3F,0xBE41,0xBE43,0xBE45,0xBE47],
        "tableBE3D/BE43; offset0/2 for low gears or4 for high-gear path")
    add("BFED", "6AD2+byte[00D9]", "TCC force-state parameter", "BFE7-BFED", range(0x6AD2,0x6AD6))
    add("C005", "6AD5+u8(byte[00D9]-1)", "TCC per-gear parameter", "BFFE-C005",
        [0x6BD4,0x6AD5,0x6AD6,0x6AD7], "resident gear0..3; no local clamp before unsigned index")
    add("C0F8 C0FC C128 C12E C144 C14B C155 C15C", "6E3B", "TCC apply transition record", "C0E8-C0EF;C271-C2D5",
        [0x6E3B], "C271 restores caller X on ordinary return; earlier C271 call consumes selected curve separately")
    add("C28A C2A4", "entry_X_at_C271", "TCC selected base curve first knot", "C277-C2A4",
        guard="C271 saves/restores X around6E2A lookup; caller supplies curve or6E3B transition record")
    add("C51A", "B319+byte[00D9]", "gear output pattern", "C514-C522", range(0xB319,0xB31D),
        "resident gear0..3; no extension/upload corruption")
    add("C751 C757", "6AB4+byte[00D9]", "TCC speed lock/unlock bounds", "C6BB-C757",
        [0x6AB5,0x6AB6,0x6AB7], "D9 nonzero, resident gear1..3")
    add("C866 C877", "D8FE_selected_pointer", "TCC cold-gain scalar", "C84D-C877;D8FE-D92D",
        guard="C3E6/C3F8 descriptor; success C=0; full selected pointer; entry B is gear or locally decremented gear")
    add("C8E8 C97D", "conversion_base+raw_ADC", "temperature conversion", "C8D6-C8E8;C96A-C97D",
        range(0xFC45,0xFE45), "baseFC45 orFD45; ADC byte0..255")
    add("CE9B", "45DB+(byte[0062]>>2)", "knock IRQ decay", "CE8F-CE9B", range(0x45DB,0x461B))
    add("CEA7", "461C+(byte[0062]>>2)", "knock IRQ gain", "CE9F-CEA7", range(0x461C,0x465C))
    add("D31C", "4058+byte[0247]", "BLM-cell emissions admission", "8D9B;D315-D31C",
        range(0x4058,0x406D), "resident BLM index0..20")
    add("D7EF", "word[entry_Y+8]+2*entry_B", "cold speed curve pointer", "D7E5-D7EF")
    add("D7FA", "word[word[entry_Y+8]+2*entry_B]", "cold speed curve first knot", "D7EF-D7FA",
        guard="nonzero pointer; F4C1 preserves X; offsets measured about128")
    add("D81B", "D8FE(word[entry_Y+6],byte[0080],entry_B).pointer", "normal speed first knot", "D805-D81B")
    add("D84A D85A", "word[entry_Y+cold_pointer_offset]+2*entry_B", "direct cold scalar pointer", "D845-D85A",
        guard="cold_pointer_offset=2 atD84A; 8 atD85A; two ABX operations do not byte-wrap their sum")
    add("D84E D85E", "word[word[entry_Y+cold_pointer_offset]+2*entry_B]", "cold scalar first byte", "D845-D85E",
        guard="offset2 atD84E; 8 atD85E; nonzero selected pointer")
    add("D86F", "D8FE(word[entry_Y+6],byte[0080],entry_B).pointer", "normal speed floor first knot", "D865-D86F")
    add("D885", "D8FE(word[entry_Y],byte[0081],entry_B).pointer", "kickdown first scalar", "D874-D885")
    add("D8AD", "word[entry_Y+2]+2*entry_B", "cold RPM offset pointer", "D8A7-D8AD")
    add("D8B1", "word[word[entry_Y+2]+2*entry_B]", "cold RPM offset word", "D8AD-D8B1", guard="nonzero pointer")
    add("D8BE", "D8FE(word[entry_Y],byte[0081],entry_B).pointer", "main RPM threshold word", "D8B4-D8BE", guard="C=0")
    add("D8E3", "entry_X+u8(2*(3*((byte[00A2]&07)>>1)+entry_B))", "range override pointer", "D8CE-D8E3")
    add("D8E7", "word[range_override_pointer_slot]", "range override scalar", "D8E3-D8E7", guard="nonzero word")
    add("D8FA", "D8FE(entry_X,byte[0080],entry_B).pointer", "fault override scalar", "D8F0-D8FA", guard="C=0")
    add("D91F", "entry_X+2+u8(2*entry_B)+k*byte[entry_X+1]", "priority descriptor pointer word", "D8FE-D92D",
        guard="k first selected bit before stop-mask test,0..7; failure row is not dereferenced")
    add("DB13", "DBE3+u8(2*byte[00D9])", "transmission spark table pointer", "DB0C-DB13",
        [0xDBE3,0xDBE5,0xDBE7,0xDBE9])
    add("DB43 DB4F DB55 DB69 DB70 DB75", "DBEB+2*(byte[00D9]-1)", "ratio spark direct pointer pairs", "DB31-DB43",
        [0xDBEB,0xDBED], "gear restricted to1 or2 before subtract/ASLB")
    add("DB48 DB58", "word[DBEB+2*(byte[00D9]-1)+4]", "ratio spark high bound scalar", "DB43-DB58")
    add("DB52", "word[DBEB+2*(byte[00D9]-1)]", "ratio spark high base scalar", "DB4F-DB52")
    add("DB6C DB78 DB7F", "word[DBEB+2*(byte[00D9]-1)+12]", "ratio spark low bound scalar", "DB69-DB7F")
    add("DB73", "word[DBEB+2*(byte[00D9]-1)+8]", "ratio spark low base scalar", "DB70-DB73")
    add("E145 E168", "5B08-j", "diagnostic candidate masks", "E132-E172", range(0x5B00,0x5B09), "j0..8")
    add("E1B8", "5AFC-j", "diagnostic lamp masks", "E1AF-E1C0", range(0x5AF4,0x5AFD), "j0..8; instruction displacement15 is added")
    add("E248", "000B+(byte[0216]>>3)", "retained diagnostic bank enumeration", "E228-E248", range(0x000B,0x0014), "0216<=71, multiple8")
    add("E24A", "5B00+(byte[0216]>>3)", "diagnostic enumeration masks", "E228-E24A", range(0x5B00,0x5B09), "0216<=71, multiple8")
    add("E262", "FE56+byte[0216]", "diagnostic flash code", "E228-E262", range(0xFE56,0xFE9F),
        "opening index0 or resident enumeration1..72; request resets index; no arbitrary mutation")
    add("E575", "E57C+4*range_row+entry_A", "range gear cap table", "E562-E575",
        guard="row=((A2&7) or6)>>1; entry_A candidate supplied byD670; no local entry_A clamp")
    add("E633 E636 E6C6 E6CA", "5B00-j", "transmission diagnostic reaction masks", "E62D-E64A;E6BC-E6DC",
        range(0x5AF8,0x5B01), "j0..8; offsets3C/33 recover5B34..3C and5B2B..33")
    add("E6D5", "entry_X+9-j", "transmission reaction category mask", "E654-E6DC",
        guard="j0..8; callers useE71F/E728/E731/E73A/E743/E74C; incoming X saved in PSHX/PULX")
    add("F175", "BC6B+u8(2*u8(byte[00D9]-1))", "long-shift diagnostic curve pointer", "F168-F175",
        [0xBC6B,0xBC6D,0xBC6F], "resident gear1..3; BMI excludes0")
    add("F2B9", "checksum_alignment_cursor", "checksum alignment prefix", "F2AA-F2C2",
        guard="generic entry_X advances to8-byte boundary; sole rooted caller71D5 uses4008 and skips prefix")
    add("F2C7 F2CB F2CF F2D3 F2D7 F2DB F2DF F2E3", "entry_X+alignment_prefix+8*j", "ROM checksum block", "71D2-71D5;F2AA-F2FC",
        range(0x4008,0x10000,8), "sole rooted caller starts4008; j0..6142 until X wraps zero")
    add("F301 F315 F318 F31B F31E", "entry_X+clear_cursor", "RAM clear helper", "F2FD-F325",
        guard="six call-specific footprints in factory_indexed_clear_calls.csv; helper entry length controls exact cursor")
    add("F4C9 F4D1 F4D9", "curve_data_base+hi(u8(coordinate)*u8(step))", "one-dimensional interpolation knot", "F4A4-F4DD",
        guard="F4C1 step16/data=entryX; F4BD subtractsB with floor0; F4B6 step=byte[X],data=X+1; F4A4 header atX,data=X+3")
    add("F509 F513 F51B", "entry_X+floor(v/16)+floor(u/16)*stride+stride", "two-dimensional second-row knot", "F4DE-F51B",
        guard="u=max(entryA-byte[X],0); v=max(entryB-byte[X+1],0); stride=byte[X+2]; instruction offset03 is header")
    add("F51F F529 F531", "entry_X+floor(v/16)+floor(u/16)*stride", "two-dimensional first-row knot", "F4DE-F531",
        guard="u=max(entryA-byte[X],0); v=max(entryB-byte[X+1],0); stride=byte[X+2]; X restored from saved row pointer")
    add("F82B F872 F876 F87A F88D FA24 FA2E", "word[0362]", "current serial descriptor field", "F822-F88D;FA21-FA30",
        guard="resident descriptor lifetime from F931/F97B/F9A5; effects of supplied code remain separate")
    add("F87D", "word[descriptor+5]+payload_index", "raw serial transmit buffer", "F87A-F87D")
    add("F888", "descriptor+u8(2*live_pointer_index)", "live serial pointer slot", "F881-F888",
        guard="index=b-1 addressed, b broadcast; pending companion byte bypasses this slot")
    add("F8B0", "word[descriptor+5]+u8(2*(b-1)+1+command04_extra)", "requested individual-address word", "F88D-F8B0",
        guard="extra=10 for command04, otherwise0; stock04 response length1 bypasses this read")
    add("F8B5", "word[descriptor+5]+1", "requested contiguous-address word", "F88D-F8B7")
    add("F8CA F8DC", "selected_transmit_address", "serial live/requested memory read", "F881-F8DC",
        guard="descriptor word, or request word plus offset; original1000..3FFF selects word; normal address&=CFFF; factory unchanged",
        kind="runtime_pointer")
    add("F931 F935", "receive_descriptor_cursor", "RX descriptor linked list", "F927-F937",
        [0x51BF,0x53A8,0x53C9,0xFBD7,0xFBE0,0xFBE9], "normal/factory list; no following zero link")
    add("F97B", "descriptor+2*received_command", "RX command descriptor word", "F96B-F97D",
        guard="first payload byte<=0A; nonzero selected word required")
    add("F9A5", "initial_page_descriptor-6+2*page_selector", "RX live-page descriptor word", "F984-F9A8",
        guard="command01 second byte; selector>=3 replaced by0; actual selector0..2")
    add("F9AB", "word[0362]", "RX buffer pointer field", "F911;F94B;F97F;F9A8-F9AB")
    add("F9AE", "word[descriptor+7]+j", "received payload byte store", "F965-F9AE",
        range(0x036C,0x038E), "all21 stock descriptors RXbase036C; j<N<=34; earlier payload writes survive abort")
    add("F9BE", "word[0362]", "accepted descriptor ID", "F9B9-F9C0")
    add("F9DC", "selected_service_block", "ordinary service selector store", "F9C3-F9DC",
        [0x038E,0x0399], "factory0050.3 clear; engine038E or transmission0399")
    add("FA16", "036C+j", "service/factory payload copy source", "FA10-FA1F", range(0x036C,0x038E), "j<N; accepted N<=34")
    add("FA18", "selected_copy_destination+j", "service/factory payload copy destination", "F9C3-FA1F",
        range(0x038E,0x03B0), "factory:038E+j,N<=34; ordinary04:038E/0399+j,N<=11; retained suffix unchanged")
    add("FAB9", "0390+j", "factory upload source", "FAB0-FAC7", range(0x0390,0x03B0), "exactly32 bytes,j0..31")
    add("FABC", "u16(word_at_FAB0[038E]+j)", "unrestricted factory upload destination", "FAB0-FAC7",
        guard="accepted factory ID01; j0..31; u16 wrap; no destination whitelist", kind="runtime_pointer")
    add("FB4F FB59 FB67", "factory_output_row", "factory output row data", "FB06-FB48;FB4A-FB69",
        [0xFBF2,0xFBF5,0xFBF8,0xFBFB,0xFBFE,0xFC01], "phase<=4F then rowFBF2+3*(phase>>4), or defaultFC01")
    add("A95B", "46EC+3*negative_input083A", "spark calibration byte", "A946-A95D", [0x46EC,0x46EF],
        guard="negative_input083A=1 for sign set, otherwise0; stock branch pruned; generic recalibrated rule retained")
    add("F5FA F611 F619 F61F F623 F625 F627", "broadcast_pointer_cursor", "optional broadcast descriptor/precopy", "F5E8-F64D",
        guard="stock schedule518F..51AF is zero; selected descriptor never reaches these PCs; generic path described in serial contract",
        kind="stock_pruned")
    return result
