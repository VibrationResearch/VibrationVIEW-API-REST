# VIC File Format

## Overview

The `.vic` file is an INI-style text configuration file with sections in square brackets (`[Section Name]`) containing key-value pairs. All sections are optional — if a section is not included, the existing value is not changed.

This file can be generated from VibrationVIEW under Configuration > Inputs using the "Save Configuration" button.

## Sections Reference

All per-channel sections use the format `Ch1=`, `Ch2=`, ..., `Ch16=` (up to 256 channels). Channel numbering is **1-based** throughout — there is no `Ch0` or `[Channel0]`.

The most commonly used sections are `[Accel Power]`, `[EnableTEDS]`, and `[Sensitivity]`.

### Hardware Configuration

| Section | Description | Values |
|---------|-------------|--------|
| `[Accel Power]` | ICP/IEPE power for accelerometer channels | `0` = off, `1` = on |
| `[Range]` | Input voltage range per channel | `-1` = autorange |
| `[Cap Coupled]` | AC-coupled input | `0` = off, `1` = on |
| `[DC Input]` | DC-coupled input | `0` = off, `1` = on |
| `[DC Offset]` | DC offset value per channel | Numeric |
| `[Single Ended]` | Single-ended vs differential input | `0` = differential, `1` = single-ended |
| `[Low Bias Voltage]` | Low bias voltage mode | `0` = off, `1` = on |
| `[Inverted]` | Invert channel polarity | `0` = normal, `1` = inverted |

### TEDS

| Section | Description | Values |
|---------|-------------|--------|
| `[EnableTEDS]` | Enable TEDS per channel (see [TEDS.md](TEDS.md)) | `0` = disabled, `1` = checked, `2` = indeterminate |
| `[Ch?TEDS]` | IEEE 1451.4 TEDS data per channel | `Pages=0`, `1=<hex data>`, `NodeID=<hardware URL>` |
| `[TEDSLength]` | Length of TEDS data per channel | Numeric |

### Sensitivity and Units

| Section | Description | Values |
|---------|-------------|--------|
| `[Sensitivity]` | Sensor sensitivity in mV per sensitivity unit | Numeric (e.g., `10`) |
| `[Channel?]` | Physical units for channel `?` (1-based) | SI base dimensions (see below) |
| `[CondSens]` | Conditioner sensitivity per channel | Numeric |
| `[UseCond]` | Use conditioner for channel | `0` = off, `1` = on |

#### Unit Definition Keys

The `[Channel?]`, `[ConditionerNumerUnit?]`, `[ConditionerDenomUnit?]`, and `[TransducerNumerUnit?]` sections share the same unit definition format using SI base dimensions:

| Key | Description | Example |
|-----|-------------|---------|
| `Meters` | Exponent for meters | `2` (for m²) |
| `Seconds` | Exponent for seconds | `-4` (for s⁻⁴) |
| `Kilograms` | Exponent for kilograms | `0` |
| `Amperes` | Exponent for amperes | `0` |
| `Kelvins` | Exponent for kelvins | `0` |
| `Moles` | Exponent for moles | `0` |
| `Candelas` | Exponent for candelas | `0` |
| `Radians` | Exponent for radians | `0` |
| `Steradians` | Exponent for steradians | `0` |
| `Name` | Display unit name | `G`, `mV`, `m`, `rad` |
| `Scaling` | Conversion factor to SI | `9.8066` (G to m/s²), `0.001` (mV to V) |
| `Offset` | Unit offset | `0` |
| `sGraphLabel` | Graph axis label | `Acceleration`, `Voltage`, `Displacement`, `Phase` |
| `Type` | Unit type identifier | `0` |

### Conditioner and Transducer Units

These sections are for optional signal conditioners, where the overall sensitivity is split into two parts: a transducer sensitivity and a conditioner sensitivity. For example, a charge-coupled accelerometer with sensitivity of pC/G (picocoulombs per G) used with a charge barrel with sensitivity of mV/pC (millivolts per picocoulomb) gives an overall sensitivity of mV/G.

| Section | Description |
|---------|-------------|
| `[TransducerNumerUnit?]` | Transducer output unit per channel (e.g., pC) |
| `[ConditionerNumerUnit?]` | Conditioner output unit per channel (e.g., mV) |
| `[ConditionerDenomUnit?]` | Conditioner input unit per channel (e.g., pC) |

### Sensor Metadata

**Note:** TEDS data will override these values when TEDS is read and applied.

| Section | Description | Values |
|---------|-------------|--------|
| `[Manufacturer]` | Sensor manufacturer | Text (e.g., `Dytran Instruments`) |
| `[Model]` | Sensor model number | Text (e.g., `3055B1`) |
| `[Serial Number]` | Sensor serial number | Text |
| `[TransducerType]` | Transducer type | Text |
| `[SensorAxis]` | Measurement axis | Text (e.g., `X`, `Y`, `Z`) |
| `[Direction]` | Measurement direction | Text |
| `[Position]` | Measurement position | Text |

### Channel Metadata

| Section | Description | Values |
|---------|-------------|--------|
| `[Channel Label]` | Display label per channel | Text (default: `Ch1`, `Ch2`, ...) |
| `[Channel Equation]` | Custom equation per channel | Text |
| `[LabID]` | Laboratory identifier per channel | Text |
| `[GUID]` | Unique identifier per channel | Text |
| `[Cond Serial Number]` | Conditioner serial number per channel | Text |
| `[CondGUID]` | Conditioner GUID per channel | Text |

## Example

An accelerometer channel configured for G-force measurement:

```ini
[Channel1]
Amperes=0
Candelas=0
Kelvins=0
Kilograms=0
Meters=2
Moles=0
Name=G
Offset=0
Radians=0
Scaling=9.8066499999999994
Seconds=-4
sGraphLabel=Acceleration
Steradians=0
Type=0
```

This defines G-force (acceleration) as the physical unit, with a scaling factor of 9.8066 to convert from G to the SI unit m/s².
