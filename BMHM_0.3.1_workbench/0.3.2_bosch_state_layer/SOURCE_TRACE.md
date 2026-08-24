# BMHM 0.3.2 source trace

This file records the stock `$31` source paths used to build the 0.3.2 state layer. Addresses refer to the BMHM/HAC source image unless noted otherwise.

## TPS: A/D to corrected engine TPS

### Raw A/D

`$F245-$F24E`

- `$F245` selects the A/D group.
- `$F24C LDAA $31,X`
- `$F24E STAA $00A6`

`$00A6` is the raw TPS A/D value.

### Learned zero / self-zero

The learned TPS-zero value is held in `$02F6` with fractional precision.

Runtime downward tracking around `$B116-$B129`:

- compare raw `$00A6` against learned `$02F6`
- when raw is below the learned value, filter the learned zero downward using calibration near `$5B25`

Startup/upward filtering around `$B1AC-$B1C5`:

- when raw TPS is above the stored zero, filter upward using calibration near `$5B27`
- clamp against the self-zero limit near `$5B24`

Runtime decel-qualified upward correction around `$B12C-$B15D`:

- uses the change in filtered VSS-derived quantity (`$00F7` versus `$00D7`)
- applies additional qualifiers and the decel threshold near `$5B2A`
- increments the learned zero by the amount near `$5B29`

The filtered VSS quantity involved in that learner is updated around `$B2A3-$B2AF`, including storage at `$0814` and the filtered state at `$00D7`.

This indirect VSS dependency remains stock in 0.3.2 and should be redesigned separately if necessary.

### Corrected TPS

`$B1CF-$B1EC`

- load learned zero `$02F6`
- round it
- subtract learned zero from raw `$00A6`
- clamp negative result to zero
- apply TPS gain `$5B26` (current value 90; approximately 0.55% per raw A/D count)
- store engine TPS at `$01A6`
- main engine processing copies the final value to `$01D9`

`$01D9` is therefore the correct state input. The 0.3.2 virtual idle switch uses `$01D9`; it does not use absolute TPS voltage.

## Closed-throttle VE selection

`$7F92-$7FB5`

Stock logic begins with corrected TPS `$01D9`, then tests the closed-throttle threshold and originally includes a VSS qualification. The consumer-level no-VSS work removed VSS authority while retaining the TPS/RPM selection.

The stock closed-throttle RPM ceiling is the literal `#72` at `$7FA4`, corresponding to 1800 RPM at 25 RPM/count.

Relevant VE surfaces:

- closed-throttle VE: `$4A88`
- open-throttle VE: `$49D5`

0.3.2 changes the TPS comparison at `$7F95` to the new virtual idle-switch exit threshold `$FF8B`, but leaves the RPM ceiling and the two-surface structure intact. This is deliberate: DECEL may use the closed-throttle VE surface without becoming TRUE IDLE.

## Stock idle classification

`$899B-$8A16`

Stock sequence:

- `$899B`: VSS qualification
- `$89A3`: load corrected TPS `$01D9`
- `$89A6`: compare against `$48DA`
- `$89AB`: set `$0050.b7` idle
- failure path through `$8A0B-$8A16` clears `$0050.b7`

The earlier no-VSS patch simply bypassed the VSS test, which caused rolling closed-throttle decel to remain classified as idle.

0.3.2 hooks `$899B -> $FEF8` and replaces the qualification with corrected-TPS plus RPM hysteresis. Success rejoins at `$89AB`; failure rejoins the stock not-idle path at `$8A0B`. Thus `$0050.b7` becomes the centralized TRUE-IDLE state.

## Existing `$0050.b7` consumers

Source walking shows the stock idle flag already feeds many engine-state decisions, including:

- transient MAP behavior near `$7DD7`
- slow O2 idle filtering near `$7E0C`
- AE differential-MAP idle threshold near `$7EC4`
- sync-fuel-at-idle behavior near `$8402`
- O2 idle/non-idle readiness around `$8644`
- O2 rich/lean thresholds around `$867A`
- proportional closed-loop idle-error scaling around `$87B0`
- P duration around `$87CB`
- integrator delay around `$885E`
- AFR/idle logic around `$8958`
- idle spark logic around `$A87E`
- manual-trans derivative behavior around `$A919`
- EGR logic around `$D0A2`
- O2 diagnostic logic around `$E489`

This broad existing fan-out is why centralizing TRUE IDLE at `$0050.b7` is cleaner than independently patching every downstream consumer.

## BLM idle cell

`$8C91-$8CCB`

Stock logic independently uses corrected TPS and VSS to decide whether to select BLM cell 16. In the earlier no-VSS patch, removing the VSS check effectively made closed TPS sufficient for cell 16, so rolling decel remained in the idle cell.

0.3.2 rewrites `$8C98-$8CA7` so cell 16 is selected only when centralized `$0050.b7` TRUE IDLE is set. Otherwise it follows the normal BLM-cell calculation path.

## IAC closed-loop qualification

`$99E2-$9A05`

Stock sequence includes:

- corrected TPS qualification at `$99E2` against `$4EF2`
- VSS qualification at `$99F2` against `$4EF3`
- failure path around `$99FA` clearing `$0036.b2`
- success at `$9A05` setting the IAC closed-loop qualification state

0.3.2 replaces the VSS decision at `$99F2` with a test of centralized `$0050.b7`. The upstream stock TPS check remains as a redundant safety qualification.

`$4E8F bit0` remains set from 0.3.1 for manual-transmission IAC behavior, preventing the automatic-transmission fallback from reasserting closed-loop idle when qualifications fail.

## Idle spark

`$A857-$A8B1`

Stock logic includes:

- VSS threshold at `$A85A` using `$415A`
- local TPS hysteresis around `$A862-$A871`, using `$415B/$415C`
- later test of `$0050.b7` around `$A87E`

The earlier 0.3.1 patch added an RPM gate outside this stock logic. 0.3.2 instead hooks `$A85A -> $FF30` and requires centralized TRUE IDLE before entering the stock downstream idle-spark routine. Failure goes to the stock idle-spark bypass path. The stock downstream checks remain intact.

## Lambda / closed-loop fuel

Stock closed-loop enable/qualification logic around `$E4FC` was already modified by the repaired closed-loop toggle patch.

0.3.2 changes the hook to `$E4FC -> $FF40` and redefines `$FE9F bit0` as `Closed Throttle Open Loop`:

- bit0 = 0: stock closed-loop eligibility
- bit0 = 1: if corrected TPS `$01D9 <= $FF8B`, clear the closed-loop/BLM enable bits and follow the open-loop path

Part load remains eligible for the existing DAMP1 controller. `$FE9F bit1` still provides the global closed-loop disable; its downstream BLM-neutralization hook near `$FEC0` and INT/P-neutralization hook near `$FEE0` remain unchanged.

## DAMP1 source areas retained unchanged

0.3.2 does not change the current closed-loop damping modifications:

- BLM timing `$48ED`
- BLM INT window `$48F7`
- P-gain region in `$4D31-$4D84`
- INT ratchet/error multiplier region `$4D85-$4D91`

The latest road-log comparison showed materially less INT displacement and short-term BPW movement, so the state-layer change is being isolated from further lambda-controller changes.

## 0.3.2 new calibration/cave allocation

- `$FEF8-$FF1F`: centralized TRUE-IDLE state routine
- `$FF30-$FF39`: idle-spark TRUE-IDLE gate
- `$FF40-$FF5E`: closed-throttle lambda gate
- `$FF60-$FF87`: intentionally unused/reserved for future AUX high-idle work
- `$FF88`: True Idle Enter RPM
- `$FF89`: True Idle Exit RPM
- `$FF8A`: Virtual Idle Switch Enter TPS
- `$FF8B`: Virtual Idle Switch Exit TPS

The code cave remains within the source-identified filler region; the coolant A/D table at `$FD45-$FE44` is not used for patches.