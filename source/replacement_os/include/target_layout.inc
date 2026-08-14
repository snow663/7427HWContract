; 7427 replacement OS target layout
; ---------------------------------
; This file contains only placement boundaries proven by the stock $31 BMHM
; image or deliberately chosen for the first replacement-ROM build.
;
; It does NOT partition all RAM or pre-assign future calibration objects.
; RAM and calibration storage are allocated as implementation actually needs
; them, while the build map remains the collision authority.

; ---------------------------------------------------------------------------
; RAM
; ---------------------------------------------------------------------------
; Stock reset loads SP=$03FF and stock code actively uses RAM below it.
; The replacement OS may allocate runtime state from low RAM as required.
;
RAM_RUNTIME_BASE        EQU     $0000
STACK_TOP               EQU     $03FF

; Stock BMHM also clears/uses $0800-$08FF. Keep this as a proven additional
; RAM resource, but do not allocate it until a module actually needs it.
RAM_AUX_BASE            EQU     $0800
RAM_AUX_END             EQU     $08FF

; ---------------------------------------------------------------------------
; ROM
; ---------------------------------------------------------------------------
; Stock BMHM calibration/header content is present at $4000+ and executable
; source begins at $7100. For the first target-linked replacement image we
; intentionally retain $7100 as the code origin so reset/vector plumbing can
; be established before the calibration region is repacked.
;
ROM_CAL_REGION_BASE     EQU     $4000
ROM_EXEC_BASE           EQU     $7100

; HC11 vector window used by the stock target.
ROM_VECTOR_BASE         EQU     $FFC0
ROM_ACTIVE_VECTOR_BASE  EQU     $FFD6
ROM_RESET_VECTOR        EQU     $FFFE
ROM_END                 EQU     $FFFF

; ---------------------------------------------------------------------------
; Policy
; ---------------------------------------------------------------------------
; 1. New runtime RAM is allocated sequentially from RAM_RUNTIME_BASE unless a
;    hardware/latency reason requires otherwise.
; 2. No permanent semantic subranges are reserved in advance.
; 3. Calibration objects receive ROM addresses when implemented.
; 4. XDF/ADX definitions describe the built ROM/packet layout; they do not
;    dictate placement ahead of implementation.
; 5. If a stock-proven hardware constraint conflicts with a provisional
;    placement, the hardware constraint wins and the map moves.
