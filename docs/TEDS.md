# TEDS Configuration

## Overview

Configuring TEDS sensors via the REST API is a multi-step process:

1. **Enable TEDS channels** — Create a `.vic` configuration file specifying which channels have TEDS sensors
2. **Upload the configuration** — Send the `.vic` file to VibrationVIEW
3. **Read and apply TEDS** — Either in one step (Option 1) or with verification (Option 2)
4. **Verify the configuration** (Optional) — Query individual channels to confirm TEDS was applied correctly

---

## Step 1: Enable Channels for TEDS

Create a client file `SendConfiguration.vic` with an `[EnableTEDS]` section. This file can also be generated from VibrationVIEW under Configuration > Inputs using the "Save Configuration" button. Sections present in this file will be applied; any missing sections will be unchanged.

### Example `SendConfiguration.vic`

```ini
[EnableTEDS]
Ch1=1
Ch2=1
Ch3=1
Ch4=1
Ch5=1
Ch6=1
Ch7=0
Ch8=0
Ch9=0
Ch10=0
Ch11=0
Ch12=0
Ch13=0
Ch14=0
Ch15=0
Ch16=0
```

- Channels set to `0` are **not** connected to TEDS sensors.
- Channels set to `1` (checked) or `2` (indeterminate) **are** connected to TEDS sensors.
- Up to 256 channels may be defined. If VibrationVIEW is configured for fewer channels, the unused entries are ignored.

## Step 2: Upload the Configuration

Send the `.vic` file via multipart form data:

```http
POST /api/v1/inputconfigurationfile HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: multipart/form-data; boundary=X-BOUNDARY
Accept: */*

--X-BOUNDARY
Content-Disposition: form-data; name=""; filename="SendConfiguration.vic"
Content-Type: application/octet-stream

[EnableTEDS]
; Using 2 (indeterminate) — channels become checked after TEDS is read
Ch1=2
Ch2=2
Ch3=2
Ch4=2
Ch5=2
Ch6=2
Ch7=0
Ch8=0
Ch9=0
Ch10=0
Ch11=0
Ch12=0
Ch13=0
Ch14=0
Ch15=0
Ch16=0
--X-BOUNDARY--
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

In the VibrationVIEW menu under Configuration > Inputs, all channels with a corresponding EnableTEDS value will appear as either checked or indeterminate. The indeterminate channels become checked as the sensors attached to the input channels are read.

## Step 3: Read and Apply TEDS

### Option 1: Read and Apply (Preferred)

Read and apply TEDS data in a single operation, without specifying what sensor is attached to each channel.

```http
POST /api/v1/tedsreadandapply HTTP/1.1
Host: 127.0.0.1:5000
Accept: */*
Content-Length: 0
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

### Option 2: Verify and Apply

Read the TEDS data first, verify the sensors are correct, then apply as separate operations.

#### Step 3a: Read TEDS

```http
GET /api/v1/tedsread HTTP/1.1
Host: 127.0.0.1:5000
Accept: */*
```

Example response:

```json
{
  "data": {
    "channel_count": 16,
    "channels": [
      {
        "channel": 1,
        "raw_value": "3C00000186B96114",
        "transducer": {
          "manufacturer": "Dytran Instruments",
          "model_number": "3056",
          "serial_no": "999998",
          "urn": "3C00000186B96114",
          "sensitivity_@_ref_cond_s_ref": { "unit": "mV/G", "value": 102.0 },
          "calibration_date": "2012-07-10T17:00:00Z",
          "..."
        }
      },
      {
        "channel": 2,
        "raw_value": "8200000C7A09F42D",
        "transducer": {
          "manufacturer": "Dytran Instruments",
          "model_number": "3055",
          "serial_no": "999999",
          "urn": "8200000C7A09F42D",
          "..."
        }
      },
      { "channel": 7, "raw_value": "Disabled" },
      { "channel": 8, "raw_value": "Disabled" }
    ],
    "success": true,
    "transducer_count": 6
  },
  "message": "TEDS read completed: 6 transducer(s) found across 16 channel(s)",
  "success": true,
  "timestamp": "2026-05-11T09:01:01.420067"
}
```

#### Step 3b: Verify and Apply TEDS

Verify the TEDS sensors are connected as expected. If correct, parse the `urn` from each channel in the response and send them as an ordered JSON array. Channels not enabled for TEDS must be set to `"Disabled"` in the JSON body.

```http
POST /api/v1/tedsverifyandapply HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: application/json
Accept: */*
```

```json
{
  "urns": [
    "3C00000186B96114",
    "8200000C7A09F42D",
    "010203040506072D",
    "020203040506072D",
    "030203040506072D",
    "040203040506072d",
    "Disabled",
    "Disabled",
    "Disabled",
    "Disabled",
    "Disabled",
    "Disabled",
    "Disabled",
    "Disabled",
    "Disabled",
    "Disabled"
  ]
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

## Step 4: Verify the TEDS Configuration (Optional)

Get TEDS information for a specific channel to confirm the configuration was applied correctly. The channel number is 1-based and passed as the first query parameter.

```http
GET /api/v1/inputtedschannel?1 HTTP/1.1
Host: 127.0.0.1:5000
Accept: */*
```

Example response:

```json
{
  "data": {
    "channel": 1,
    "internal_channel": 0,
    "result": [
      {
        "Channel": 1,
        "Teds": [
          ["Manufacturer", "Dytran Instruments", ""],
          ["Model number", "3056", ""],
          ["Version letter", "B", ""],
          ["Serial no.", "999998", ""],
          ["Sensitivity @ ref. cond. (S ref)", "102.0 mV/G", "mV/G"],
          ["High pass cut-off frequency (F hp)", "0.313 Hz", "Hz"],
          ["Sensitivity direction (x,y,z, n/a)", "X", ""],
          ["Transducer weight", "7.95 gm", "gm"],
          ["Polarity (Sign)", "+1", ""],
          ["Low pass cut-off frequency (F lp)", "33 kHz", "kHz"],
          ["Resonance frequency (F res)", "31.8 kHz", "kHz"],
          ["Calibration date", "2012-07-10T17:00:00Z", ""],
          ["Calibration initials", "FC ", ""],
          ["Calibration Period", "365 days", "days"]
        ]
      }
    ],
    "success": true
  },
  "message": "TEDS information retrieved for channel 1 (1-based)",
  "success": true,
  "timestamp": "2026-05-11T09:19:17.065857"
}
```

Each TEDS entry is a 3-element array: `[name, value, unit]`. The unit is an empty string when not applicable.