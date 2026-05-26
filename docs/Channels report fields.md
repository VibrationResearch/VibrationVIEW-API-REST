# `POST /api/v1/reportfields` — Per-Channel Fields Reference

Wraps the VibrationVIEW COM method `ReportFields(fields)`. Retrieves multiple report field values in a single call, with optional per-channel expansion.

Use `channel=all` with per-channel field names to document and verify the complete input configuration — including transducer settings (IEPE, coupling, differential, loopback, DC offset), channel configuration (range, status), calibration status (accelerometer and conditioner dates, age, remaining), and TEDS data.

**Method:** `POST`
**COM method:** `IVibrationVIEW::ReportFields(BSTR fields) → SAFEARRAY`
**Source:** `routes/reporting.py` → `report_fields()`

---

## Request

### Field selection

| Mode | Format |
|---|---|
| JSON string | `{"fields": "ChName,ChStatus,TEDS"}` |
| JSON array | `{"fields": ["ChName", "ChStatus", "TEDS"]}` (joined with commas server-side) |

Field names are case-sensitive and must match VibrationVIEW report field names. Missing/empty `fields` returns HTTP 400 with `MISSING_PARAMETER`.

### Channel expansion (`channel=all`) — preferred

Use `?channel=all` to expand each field across all hardware input channels. The server strips trailing digits from each field name to derive the base key, expands it across all channels (`GetHardwareInputChannels()`), and returns `results` as an object keyed by channel number.

- `ChName` → key `ChName` → expands to `ChName1..ChNameN`
- `TEDS` → key `TEDS` → expands to `TEDS1..TEDSN`

Per-channel fields require either `channel=all`, an explicit index suffix (e.g. `ChName1`), or `*|` wildcard. Without one, COM returns `"n/a"`.

### Wildcard syntax (`*|`)

Appending `*|` to a field name asks VibrationVIEW itself to expand across all channels (handled COM-side, not by the Flask layer).

Example: `ChAccelRMS*|` returns all channel accelerometer RMS values.

**Wildcard `*|` and `channel=all` are mutually exclusive — do not combine.**

---

## Response envelope

All responses follow the standard envelope:

```json
{
  "success": true,
  "message": "ReportFields executed successfully",
  "timestamp": "2026-05-20T13:49:55.795272",
  "data": { ... }
}
```

| Field | Type | Notes |
|---|---|---|
| `success` | bool | Transport/handler-level success. `true` even when COM returns empty/no-data. |
| `message` | string | Human-readable status. Always `"ReportFields executed successfully"` on the success path. |
| `timestamp` | string | ISO 8601 server timestamp. |
| `data` | object | Payload — see below. |

### `data` object

| Field | Type | Always present? | Description |
|---|---|---|---|
| `executed` | bool | yes | `true` when the COM call returned without raising. |
| `fields_string` | string | yes | The post-expansion, comma-delimited field list actually sent to `ReportFields`. When `channel=all` is used, this is the *expanded* list, not the caller's input. |
| `results` | array or object | yes | Without `channel=all`: flat array of values from COM, one entry per field in `fields_string`. With `channel=all`: object keyed by channel number (string keys `"1"..."N"`), each mapping base field name → parsed value with the redundant `{Field}{N}` prefix stripped. |

### Result element shape

Each element of `results` may be:

- **A `[name, value]` pair** (most common) — `["ChName1", "Ch1"]`, `["mVg1", "102 mV/G"]`
- **A 2D array** when the COM value was a tab/CRLF-delimited string (TEDS, sometimes others). The route parses `\t`-separated columns and `\r\n`-separated rows, stripping a single trailing tab per row. Example:
  ```json
  [["Manufacturer", "Dytran Instruments"], ["Model number", "3056"], ...]
  ```
- **A scalar string** for fields that come back as plain strings (e.g. `"TEDS data not available"`).

### `results` object (when `channel=all`)

For each result entry, the route computes:

```
channel  = (i % num_channels) + 1
base     = base_fields[i // num_channels]
```

It then strips the redundant field prefix:

- `["ChManufacturer1", "Dytran Instruments"]` → `"Dytran Instruments"`
- `[["ChManufacturer1", "Dytran Instruments"]]` → `"Dytran Instruments"`
- Anything else is stored as-is.

So each `results.<N>` is a dictionary keyed by base field name with the cleaned-up value.

---

## Per-channel field reference

Observed values for common channel fields (non-exhaustive — driven by VibrationVIEW report field schema):

| Field | Notes |
|---|---|
| `ChName` | Display name, e.g. `"Ch1"` |
| `ChStatus` | Input status: `"Ok"`, `"IEPE"`, `"Input is OPEN"`, others possible |
| `ChStatusTeds` | TEDS state: `"TEDS ok"`, `"Disabled"`, `"No TEDS"`, `"New connection"`, `"TEDS error"`, etc. |
| `ChManufacturer` | From TEDS or manual config; `""` when not set |
| `ChModel` | Includes version suffix (e.g. `"3056B2"`) |
| `ChSerialNumber` | `""` when not set |
| `mVg` | Sensitivity with units in the string (e.g. `"102 mV/G"`) |
| `Cal` | Calibration — Accelerometer serial number and calibration |
| `ChAcp` | Transducer — IEPE Power Source Enable |
| `ChCoup` | Transducer — Input Capacitor Coupled |
| `ChLoopback` | Transducer — Input Diagnostic Loopback |
| `ChDiff` | Transducer — Input Differential |
| `ChCalDate` | Calibration — Accelerometer calibration |
| `ChCalDue` | Calibration — Accelerometer calibration due date |
| `ChCalRemain` | Calibration — Accelerometer days since calibration |
| `ChCalAge` | Calibration — Accelerometer days until calibration scheduled |
| `ChCondCalDate` | Calibration — Conditioner calibration |
| `ChCondCalDue` | Calibration — Conditioner calibration due date |
| `ChCondCalRemain` | Calibration — Conditioner days since calibration |
| `ChCondCalAge` | Calibration — Conditioner days until calibration scheduled |
| `ChDCOffset` | Transducer — DC Offset |
| `ChRange` | Channel — Range |
| `TEDS` | Array of `[label, value]` pairs when programmed; literal `"TEDS data not available"` otherwise |

### TEDS sub-fields (IEEE 1451.4 Template 25 accelerometer)

When present, `TEDS` is a 2D array containing these label/value pairs in order:

`Manufacturer`, `Model number`, `Version letter`, `Version number`, `Serial no.`, `Sensitivity @ ref. cond. (S ref)`, `High pass cut-off frequency (F hp)`, `Sensitivity direction (x,y,z, n/a)`, `Transducer weight`, `Polarity (Sign)`, `Low pass cut-off frequency (F lp)`, `Resonance frequency (F res)`, `Quality factor @ F res (Q)`, `Amplitude slope (a)`, `Temperature coefficient (b)`, `Reference frequency (F ref)`, `Reference temperature (T ref)`, `Calibration date` (ISO 8601), `Calibration initials`, `Calibration Period`, `Measurement position ID`, `User data (ascii 7-bit)`.

Other TEDS templates (microphone, force, etc.) return different label sets.

---

## Examples

### Example 1 — All channels (preferred)

```http
POST /api/v1/reportfields?channel=all
Content-Type: application/json

{"fields": ["ChName", "ChStatus", "ChStatusTeds", "mVg", "ChManufacturer", "ChModel", "ChSerialNumber", "TEDS"]}
```

Response (abridged, 4-channel system, Ch1 has a TEDS sensor):

```json
{
  "success": true,
  "message": "ReportFields executed successfully",
  "timestamp": "2026-05-26T14:55:14.160954",
  "data": {
    "executed": true,
    "fields_string": "ChName1,ChName2,...,ChName4,ChStatus1,...,TEDS4",
    "results": {
      "1": {
        "ChName": "Ch1",
        "ChStatus": "Input is OPEN",
        "ChStatusTeds": "New connection",
        "mVg": "112.3 mV/G",
        "ChManufacturer": "Kistler Instrument Corporation",
        "ChModel": "8768A50",
        "ChSerialNumber": "6421616",
        "TEDS": [
          ["Manufacturer", "Kistler Instrument Corporation"],
          ["Model number", "8768"],
          ...
          ["User data (ascii)"]
        ]
      },
      "2": {
        "ChName": "Ch2",
        "ChStatus": "Ok",
        "ChStatusTeds": "Disabled",
        "mVg": "10 mV/G",
        "ChManufacturer": "",
        "ChModel": "",
        "ChSerialNumber": "",
        "TEDS": "TEDS data not available"
      }
    }
  }
}
```

### Example 2 — Explicit channel index

```http
POST /api/v1/reportfields
Content-Type: application/json

{"fields": ["ChName1", "ChStatus1", "TEDS1"]}
```

```json
{
  "success": true,
  "message": "ReportFields executed successfully",
  "timestamp": "2026-05-26T14:59:31.464694",
  "data": {
    "executed": true,
    "fields_string": "ChName1,ChStatus1,TEDS1",
    "results": [
      ["ChName1", "Ch1"],
      ["ChStatus1", "Input is OPEN"],
      ["TEDS1", [["Manufacturer", "Kistler Instrument Corporation"], ["Model number", "8768"], ..., ["User data (ascii)"]]]
    ]
  }
}
```

### Example 3 — Wildcard (COM-side expansion)

```http
POST /api/v1/reportfields
Content-Type: application/json

{"fields": ["ChAccelRMS*|", "ChDisplacement*|"]}
```

`fields_string` is sent verbatim to COM (`"ChAccelRMS*|,ChDisplacement*|"`); the COM layer handles channel expansion. `results` is a flat array.

---

## Errors

### 400 — Missing fields

When the resolved `fields_string` is empty after parsing:

```json
{
  "success": false,
  "error": {
    "code": "MISSING_PARAMETER",
    "message": "Missing required parameter: fields"
  }
}
```

Reproduces when:
- POST with no body, or body missing the `fields` key, or `fields: ""`

### 500 — COM dispatch failure

Any exception raised by `vv_instance.ReportFields(...)` propagates through `@handle_errors`, which produces a 500 with the COM error code, HRESULT, and help_context surfaced via `extract_com_error_info`. The `/reportfields` route does **not** have the `VVIEW_E_NO_DATA` / `VVIEW_E_ALREADY_RUNNING` shortcuts that `/reportfieldshistory` and `/reportvectorhistory` use — failures here are reported as errors, not as empty success responses.

---

## Implementation notes

- `executed: true` mirrors `success: true` on the happy path — they're redundant for this endpoint. The field exists for parity with other reporting endpoints that have additional execution branches.
- When `channel=all` is used, `results` is an object keyed by channel number. Without it, `results` is a flat array.
- `ChStatus = "IEPE"` and `ChStatusTeds = "Disabled"` is a valid combination — IEPE current can be on while TEDS reading is configured off.
- Calibration dates in TEDS are programmed once on the sensor and don't auto-update; a stale `Calibration date` doesn't imply a bug.
