; 7427 replacement OS - HAL-private RAM
; -------------------------------------
; Included only while the master build is in its RAM allocation section.
;
; Policy: add HAL-private state only when a HAL module actually needs it.
; Do not pre-partition future RAM. The assembled map is the collision authority.

HAL_RAM_BEGIN:

HAL_ADC_TIMEOUT:        RMB     1

; Eight-byte native ISR gateway, byte layout enforced by host contract.
; This RAM is NOT a second copy of the factory $0000..$08FF variables.
HAL_ISR_VECTOR_HI:      RMB     1
HAL_ISR_VECTOR_LO:      RMB     1
HAL_ISR_CCR_ADDR_HI:    RMB     1
HAL_ISR_CCR_ADDR_LO:    RMB     1
HAL_ISR_STATUS:         RMB     1
HAL_ISR_ACTION:         RMB     1
HAL_ISR_BUSY:           RMB     1
HAL_ISR_PROOF:          RMB     1

HAL_RAM_END:
