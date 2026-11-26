# 7427 Configurator

Configure and rebuild the GM 16197427 BMHM $31 stock image from a saved project.

## Open the configurator

1. Extract the application folder.
2. In that folder run `python3 app.py` (Windows: `py -3 app.py`). Python 3.10 or newer is sufficient.
3. In the browser, choose the factory BMHM BIN. The app accepts the 48 KiB mapped image or the 64 KiB image padded with erased bytes.
4. Select changes, click **Preview**, and use **Save project** to keep the settings. **Export build** downloads the BIN, XDF, project JSON and byte-change report.

The app runs locally at `http://127.0.0.1:8742/`. Use `--port` to change the port. The input ROM stays in the browser session and local build server memory. Bring the original ROM again when reopening a project. The application bundle does not include a factory BIN.

For repeatable builds outside the browser:

```sh
python3 configurator.py stock.bin 7427-project.json 7427-build.zip
```

## First supported edits

| Control | ROM behavior |
|---|---|
| Burst spark | Sets or clears `$400F.3`, preserving the other factory options in that byte. |
| Burst spark gain | Edits the eight cells at `$46E4–$46EB` (nominal 75–110 °C). The XDF uses raw values. The lookup reads `$46EC` as an interpolation neighbor at the stock cap, and dynamic spark owns that byte. |
| Base spark table placement | Swap the two 292-byte base-spark blocks to verify relocation. The build updates both stock LDX operands, the XDF addresses, and the byte-change report from the same placement map. |
| Slot 00 | Keeps or removes the `JSR $CF15` at `$7AA9`, where the stock target is a single RTS. The inline option accepts selected register and immediate instructions fitting in three bytes and pads unused bytes with NOPs. Execution continues at the existing RTS at `$7AAC`. |
| Custom tables | Resize a raw byte grid while retaining overlapping cells. New cells start at zero. The build exports ASM11-compatible table source with row, column and stride symbols. |
| Custom assembly | Paste or import an assembly module, then export it alongside the table source and project. |

Custom tables and larger assembly modules remain drafts until they have reviewed ROM placements and consumers. The inline hook permits user-supplied register and condition-code effects. Preview verifies encoding and placement. Runtime behavior of custom instructions needs separate verification.

A stock configuration reproduces the factory image. Changed builds recalculate the checksum at `$4006` and record the original and replacement bytes for each edit. The generated XDF covers the burst curve and both base-spark grids. Base-spark XDF axes use raw lookup coordinates.

The decoder and compact assembler are reused from `tools/factory_rom_decode.py` and `tools/manual_idle_asm.py` in 7427HWContract at `8fba3b6`. The inline editor deliberately exposes a small subset. No separate ASM11 installation is required for this scope.

Under **Stock calibration → Base spark table placement**, select **Swap table locations** and preview the old and new addresses. The proof moves the stock open-throttle header from `$4166` to `$428A` and the closed-throttle header in the other direction. Both slots are exactly the same size. This proof leaves each stock table's 17 × 17 geometry intact. Larger tables still require a reviewed allocation and lookup changes.

Older projects default to factory placement. Older projects with 11 curve cells are accepted when their final three cells match the factory dynamic-spark bytes. Exports save the corrected eight-cell geometry.

## Tests

```sh
python3 -m unittest discover -s tests -v
BMHM_STOCK_BIN=/path/to/stock.bin python3 -m unittest discover -s tests -v
python3 tests/replay_spark_relocation.py /path/to/stock.bin /path/to/7427HWContract
```
