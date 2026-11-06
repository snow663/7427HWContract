# HC11 console source

Implementation target: staged $F5 input -> validated command queue -> retired scheduler service -> bounded INFO/READ/GATHER/CLOSE -> prepared response using existing SCI TX driver.

Source pending ROM/RAM access and ownership audit. Do not patch the current Rev B calibration in place.
