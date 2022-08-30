
## Pioreactor LED calibration plugin

![CI tests](https://github.com/kellytr/pioreactor-led-calibration-plugin/actions/workflows/ci.yaml/badge.svg)

The LED automations available on the Pioreactor are limited: light intensity percentages are based on the power supplied to the LED wires. For specific research and for comparing results between Pioreactors, this plugin can be used to determine the exact LED intensity values.

This plugin offers the ability to calibrate your LEDs using an **external light probe**. It functions in two parts: 1) a command line calibration that creates a line-of-best-fit and 2) a calibrated light/dark cycle automation available on the Pioreactor web interface. 

## Installation and use instructions

Install from the command line.

```
pio install-plugin led-calibration-plugin  ## to install on a single Pioreactor 

## OR, on the command line of the leader Pioreactor

pios install-plugin led-calibration-plugin ## to install on all Pioreactors in a cluster
```

This plugin is also available on the Pioreactor web interface, in the _Plugins_ tab. Downloading from the web interface will install on all Pioreactors in a cluster.

Then run the calbration by typing into your command line:

```
pio run led_calibration
```

To perform this calibration, insert your vial containing media into the Pioreactor and submerge your light probe. Follow the prompts on the command line. The plugin will increase the light intensity, and prompt you to record the readings from your light probe. A calibration line of best fit will be generated based on your light probe readings. 

An automation will become available on the web interface. In the _Pioreactors_ tab, under _Manage_, you can _Start_ an _LED automation_. A new option becomes available in the drop-down menu called "Calibrated Light/Dark Cycle". To use this automation, use two LED cables in each of channels C and D, and insert the bulbs into the X2 and X3 pockets on the Pioreactor vial holder. **Calibrations for LEDs in channels "C" and "D" must exist.** Once set up, input your desired light intensity in AU (ex. 1000 AU). The automation will set the percent light intensity such that an output of 1000 AU occurs on both LEDs.

## Subcommands 

Run a subcommand by typing the following into the command line: 
```
pio run led_calibration <SUBCOMMAND>
```
The following subcommands are available:

### **list**
Prints a table with all existing calibrations stored on the leader. Headings include unique names, timestamps, and channels.

| Name | Timetamp | Channel |
|------|----------|---------|
| Algae_C_2022 | 2022-08-29T20:12:00.400000Z | C |
| Algae_B_2022 | 2022-08-29T20:13:00.400000Z | B |
| Algae_B_2021 | 2021-08-29T20:15:00.400000Z | B |

### **display_current**
Displays the graph and data for the current calibration for each channel A, B, C, and D, if it exists. For example, for the data above, the current calibrations for Algae_C_2022 and Algae_B_2022 will be displayed. 

### **change_current**
If you would like to change a current calibration to a previous one, use `change_current <UNIQUE NAME>`. These changes are based on the channel assigned to the calibration. 

For example: 
`pio run led_calibration change_current Algae_B_2021` would replace Algae_B_2022, since only one calibation is active per channel. 

## When to perform an LED calibration

Calibrations should be performed on a case-by-case basis. A new calibration must be performed per channel, and/or for new LED cables, and with any change in media that can alter the light intensity within the vial.  

## Plugin documentation 

Documentation for plugins can be found on the [Pioreactor wiki](https://docs.pioreactor.com/developer-guide/intro-plugins).
