; 7427 replacement OS - HAL-private RAM
; -------------------------------------
; Included only while the master build is in its RAM allocation section.
;
; Policy: add HAL-private state only when a HAL module actually needs it.
; Do not pre-partition future RAM. The assembled map is the collision authority.

HAL_RAM_BEGIN:

HAL_ADC_TIMEOUT:        RMB     1

HAL_RAM_END:
