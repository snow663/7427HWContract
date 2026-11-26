"use strict";

const $ = (id) => document.getElementById(id);
const emptyProject = () => ({
  version: 1, burst_spark: "stock", burst_curve: null, spark_layout: "stock",
  slot_00: { mode: "stock", assembly: "" }, custom_assembly: "", tables: [],
});
let project = emptyProject();
let rom = null;
let stockCurve = null;
const curveTemperatures = [75, 80, 85, 90, 95, 100, 105, 110];
let revision = 0;

function element(tag, text) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  return node;
}

function status(text, isError = false) {
  $("status").textContent = text;
  $("status").dataset.error = isError;
}

function changed() {
  revision++;
  $("report").replaceChildren();
  status(rom ? "Configuration changed. Preview to see the ROM edits." : "Choose a stock image to preview this project.");
}

function field(type, value, label, update, min, max) {
  const input = element("input");
  Object.assign(input, { type, value });
  input.setAttribute("aria-label", label);
  if (type === "number") Object.assign(input, { min, max, step: 1, required: true });
  input.className = "editable";
  input.addEventListener("input", () => {
    update(type === "number" ? input.valueAsNumber : input.value);
    changed();
  });
  return input;
}

function button(text, action) {
  const item = element("button", text);
  item.addEventListener("click", action);
  return item;
}

function showCurve() {
  const host = $("curve");
  const values = project.burst_curve ?? stockCurve;
  host.replaceChildren();
  if (!values) {
    host.append(element("p", "Load the stock image to see its curve."));
    return;
  }
  values.forEach((value, index) => {
    const label = element("label", curveTemperatures[index] + " °C");
    label.className = "cell";
    label.append(field("number", value, "Burst curve at " + curveTemperatures[index] + " °C", (newValue) => {
      if (!project.burst_curve) project.burst_curve = [...stockCurve];
      project.burst_curve[index] = newValue;
    }, 0, 255));
    host.append(label);
  });
}

function resizeTable(table, rows, cols) {
  const cells = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      cells.push(r < table.rows && c < table.cols ? table.cells[r * table.cols + c] : 0);
    }
  }
  Object.assign(table, { rows, cols, cells });
}

function control(label, input) {
  const node = element("label", label);
  node.append(input);
  return node;
}

function showTables() {
  const list = $("tables");
  list.replaceChildren();
  project.tables.forEach((table, index) => {
    const card = element("div");
    card.className = "draft-table";
    const controls = element("div");
    controls.className = "table-controls";
    const name = field("text", table.name, "Table name", (value) => { table.name = value; });
    Object.assign(name, { pattern: "[A-Za-z][A-Za-z0-9_]{0,30}", required: true, maxLength: 31 });
    const rows = field("number", table.rows, "Rows", () => {}, 1, 16);
    const cols = field("number", table.cols, "Columns", () => {}, 1, 16);
    controls.append(control("Name", name), control("Rows", rows), control("Columns", cols),
      button("Resize", () => {
        if (!rows.reportValidity() || !cols.reportValidity()) return;
        resizeTable(table, rows.valueAsNumber, cols.valueAsNumber);
        showTables();
        changed();
      }),
      button("Remove table", () => {
        project.tables.splice(index, 1);
        showTables();
        changed();
      }));
    const grid = element("table");
    grid.className = "custom-grid";
    const headings = grid.createTHead().insertRow();
    headings.append(element("th"));
    for (let c = 0; c < table.cols; c++) headings.append(element("th", String(c + 1)));
    const body = grid.createTBody();
    for (let r = 0; r < table.rows; r++) {
      const row = body.insertRow();
      row.append(element("th", String(r + 1)));
      for (let c = 0; c < table.cols; c++) {
        const offset = r * table.cols + c;
        row.insertCell().append(field("number", table.cells[offset], "Row " + (r + 1) + ", column " + (c + 1),
          (value) => { table.cells[offset] = value; }, 0, 255));
      }
    }
    const wrap = element("div");
    wrap.className = "grid-wrap";
    wrap.append(grid);
    card.append(controls, wrap);
    list.append(card);
  });
  $("add-table").disabled = project.tables.length >= 16;
}

function showProject() {
  $("burst").value = project.burst_spark;
  $("spark-layout").value = project.spark_layout;
  $("slot").value = project.slot_00.mode;
  $("inline-code").value = project.slot_00.assembly;
  $("inline-pane").hidden = project.slot_00.mode !== "inline";
  $("draft-code").value = project.custom_assembly;
  showCurve();
  showTables();
}

function validateProject(value) {
  const sameKeys = (object, keys) => object && typeof object === "object" && !Array.isArray(object) &&
    Object.keys(object).length === keys.length && keys.every((key) => Object.hasOwn(object, key));
  const bytes = (cells, size) => Array.isArray(cells) && cells.length === size &&
    cells.every((n) => Number.isInteger(n) && n >= 0 && n <= 255);
  const source = (text) => typeof text === "string" && text.length <= 16000;
  const dimension = (n) => Number.isInteger(n) && n >= 1 && n <= 16;
  if (!sameKeys(value, Object.keys(emptyProject())) || value.version !== 1 ||
      !["stock", "enabled", "disabled"].includes(value.burst_spark) ||
      !["stock", "swap"].includes(value.spark_layout) ||
      !(value.burst_curve === null || bytes(value.burst_curve, curveTemperatures.length)) ||
      !sameKeys(value.slot_00, ["mode", "assembly"]) ||
      !["stock", "remove", "inline"].includes(value.slot_00.mode) ||
      !source(value.slot_00.assembly) || !source(value.custom_assembly) ||
      !Array.isArray(value.tables) || value.tables.length > 16 ||
      !value.tables.every((t) => sameKeys(t, ["name", "rows", "cols", "cells"]) &&
        typeof t.name === "string" && /^[A-Za-z][A-Za-z0-9_]{0,30}$/.test(t.name) &&
        dimension(t.rows) && dimension(t.cols) && bytes(t.cells, t.rows * t.cols)) ||
      new Set(value.tables.map((t) => t.name.toUpperCase())).size !== value.tables.length) {
    throw new Error("Select a valid version 1 configurator project.");
  }
}

async function request(path, data) {
  const response = await fetch("/api/" + path, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error((await response.json()).error);
  return response;
}

function download(blob, name) {
  const url = URL.createObjectURL(blob);
  const link = element("a");
  Object.assign(link, { href: url, download: name });
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function showReport(report) {
  const host = $("report");
  const draftCount = report.draft_table_count + Number(report.draft_assembly);
  host.replaceChildren(element("p", draftCount ? draftCount + " draft sources exported separately." : ""));
  for (const move of report.relocations) {
    const block = element("article");
    block.append(element("strong", move.title),
      element("p", move.from + " → " + move.to + " · " + move.size + " bytes"),
      element("code", "ROM operand " + move.operand_address + " · XDF cells " + move.xdf_address));
    host.append(block);
  }
  for (const change of report.changes) {
    if (change.reason.startsWith("Relocate ")) continue;
    const block = element("article");
    block.append(element("strong", change.address), element("p", change.reason),
      element("code", change.before + " → " + change.after));
    host.append(block);
  }
  const identity = element("article");
  identity.append(element("p", "Output SHA-256"), element("code", report.image_sha256));
  host.append(identity);
}

function validFields() {
  return [...document.querySelectorAll(".editable")].every((item) => item.reportValidity());
}

let building = false;
async function run(action) {
  if (building || !validFields()) return;
  building = true;
  const submitted = revision;
  $("preview").disabled = $("build").disabled = true;
  try {
    const response = await request(action, { rom, project });
    if (action === "preview") {
      const report = await response.json();
      if (revision !== submitted) return;
      showReport(report);
      status(report.changed_bytes ? report.changed_bytes + " ROM bytes changed." : "Output matches the factory image byte for byte.");
    } else {
      download(await response.blob(), "7427-build.zip");
      status(revision === submitted ? "Build exported." : "Earlier configuration exported. Preview the current edits to see their changes.");
    }
  } catch (error) {
    status(error.message, true);
  } finally {
    building = false;
    $("preview").disabled = $("build").disabled = !rom;
  }
}

$("open-rom").onclick = () => $("rom-file").click();
$("import-assembly").onclick = () => $("assembly-file").click();
$("assembly-file").onchange = async (event) => {
  const file = event.target.files[0];
  event.target.value = "";
  if (!file) return;
  try {
    if (file.size > 64000) throw new Error("Assembly must be at most 16,000 characters.");
    const source = await file.text();
    if (source.length > 16000) throw new Error("Assembly must be at most 16,000 characters.");
    project.custom_assembly = $("draft-code").value = source;
    changed();
  } catch (error) {
    status(error.message, true);
  }
};
$("open-project").onclick = () => $("project-file").click();
$("rom-file").onchange = async (event) => {
  const file = event.target.files[0];
  event.target.value = "";
  if (!file) return;
  try {
    if (![49152, 65536].includes(file.size)) throw new Error("Select a 48 KiB or 64 KiB BMHM stock BIN.");
    const bytes = new Uint8Array(await file.arrayBuffer());
    let raw = "";
    for (let i = 0; i < bytes.length; i += 8192) raw += String.fromCharCode(...bytes.subarray(i, i + 8192));
    const candidate = btoa(raw);
    const response = await request("identify", { rom: candidate });
    stockCurve = (await response.json()).curve;
    rom = candidate;
    $("rom-label").textContent = file.name + " · Factory SHA-256 verified";
    $("preview").disabled = $("build").disabled = false;
    showCurve();
    changed();
  } catch (error) {
    status(error.message, true);
  }
};
$("project-file").onchange = async (event) => {
  const file = event.target.files[0];
  event.target.value = "";
  if (!file) return;
  try {
    const value = JSON.parse(await file.text());
    if (value?.version === 1 && !Object.hasOwn(value, "spark_layout")) value.spark_layout = "stock";
    if (value?.version === 1 && Array.isArray(value.burst_curve) && value.burst_curve.length === 11) {
      if (value.burst_curve.slice(8).some((cell) => cell !== 0)) {
        throw new Error("This old project changes adjacent dynamic-spark bytes. Restore its factory curve and re-enter the first eight values.");
      }
      value.burst_curve = value.burst_curve.slice(0, 8);
    }
    validateProject(value);
    project = value;
    showProject();
    changed();
  } catch (error) {
    status(error.message, true);
  }
};
$("save-project").onclick = () => {
  try {
    validateProject(project);
    download(new Blob([JSON.stringify(project, null, 2) + "\n"], { type: "application/json" }), "7427-project.json");
  } catch (error) {
    status(error.message, true);
  }
};
$("burst").onchange = (event) => { project.burst_spark = event.target.value; changed(); };
$("spark-layout").onchange = (event) => { project.spark_layout = event.target.value; changed(); };
$("slot").onchange = (event) => {
  project.slot_00.mode = event.target.value;
  $("inline-pane").hidden = project.slot_00.mode !== "inline";
  changed();
};
$("inline-code").oninput = (event) => { project.slot_00.assembly = event.target.value; changed(); };
$("draft-code").oninput = (event) => { project.custom_assembly = event.target.value; changed(); };
$("stock-curve").onclick = () => { project.burst_curve = null; showCurve(); changed(); };
$("add-table").onclick = () => {
  let index = 1;
  const used = new Set(project.tables.map((table) => table.name.toUpperCase()));
  while (used.has("TABLE_" + index)) index++;
  project.tables.push({ name: "TABLE_" + index, rows: 2, cols: 2, cells: [0, 0, 0, 0] });
  showTables();
  changed();
};
$("preview").onclick = () => run("preview");
$("build").onclick = () => run("build");
showProject();
