
## Pioreactor LED calibration plugin

![CI tests](https://github.com/kellytr/pioreactor-led-calibration-plugin/actions/workflows/ci.yaml/badge.svg)

This plugin offers the ability to calibrate your LEDs using an external light probe.

To perform this calibration, insert your vial containing media into the Pioreactor and submerge your light probe. The plugin will increase the light intensity, and prompt you to record the readings from your light probe. A calibration line of best fit will be generated based on your light probe readings.

An automation will become available on the web interface called "Calibrated Light/Dark Cycle". To use this automation, calibrations for LEDs in channels "C" and "D" must exist. Input your desired light intensity in AU (ex. 1000 AU). The automation will set the percent light intensity such that an output of 1000 AU occurs on both LEDs.

## Installation instructions

Install from the command line.

```
pio install-plugin led-calibration-plugin
```

Then run by typing into your command line:

```
pio run led_calibration
```
