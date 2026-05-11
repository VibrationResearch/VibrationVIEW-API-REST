# Loading a Test Profile

## Overview

Loading and running a test profile via the REST API can be done in several ways:

1. **Open a profile** — Load a profile without starting it (`/opentest`)
2. **Start the test** — Start an already-loaded profile (`/starttest`)
3. **Run a profile** — Open and start in one step (`/runtest`)
4. **List open profiles** — See which profiles are currently loaded (`/listopentests`)
5. **Close a profile** — Close an open profile tab (`/closetest`)

Profile files are stored in the VibrationVIEW Profiles folder (configured via `PROFILE_FOLDER` in `.env`).

---

## Open a Profile

Load a test profile without starting it. The test can then be started with `/starttest`.

- **COM Method:** `OpenTest(filepath)`
- **Methods:** `POST`, `PUT`, `GET`

### POST/PUT: Upload and Open a File

There are three ways to use POST/PUT:

**Option 1 — Multipart form data (recommended):**

Upload a profile file from the client computer to VibrationVIEW. The original filename is auto-detected from the form field.

```http
POST /api/v1/opentest HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: multipart/form-data; boundary=X-BOUNDARY
Accept: */*
Content-Length: 269440

--X-BOUNDARY
Content-Disposition: form-data; name="file"; filename="Random_Profile.vrpj"
Content-Type: application/octet-stream

{
    "Version": "2025.1",
    "Writer": "VibrationVIEW-2025.4.3-f65f336d6",
    "TestType": "Random",
    "ActiveChannels": 16,
    "TestDefinition": {
        "ControlUnit": "G",
        "Schedule": [
            {
                "Type": "Run",
                "Duration": { "Value": 3600, "Unit": "sec" },
                "Modifier": { "Value": 20, "Unit": "%" },
                ...
            }
        ],
        ...
    }
}
--X-BOUNDARY--
```

Profile files are JSON documents (`.vrpj` extension for newer profiles, `.vsp` for legacy).

**Option 2 — Raw binary body:**

The filename must be provided as a query parameter.

```http
POST /api/v1/opentest?filename=test1.vsp HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: application/octet-stream

<binary file content>
```

**Option 3 — Open existing file (no upload):**

If no file content is included in the body, the file is opened by path from a folder accessible to VibrationVIEW on the server (same as GET).

```http
POST /api/v1/opentest?filename=test1.vsp HTTP/1.1
Host: 127.0.0.1:5000
Accept: */*
```

**Note:** When uploading, if a profile with the same name is already open, the existing tab is automatically closed before opening the new file.

### GET: Open an Existing File

GET is supported for convenience when testing from a web browser, but POST/PUT is the recommended approach. Opens a file by path from a folder accessible to VibrationVIEW on the server.

```http
GET /api/v1/opentest?filename=test1.vsp HTTP/1.1
Host: 127.0.0.1:5000
Accept: */*
```

The filename can also be passed as an unnamed query parameter:

```http
GET /api/v1/opentest?test1.vsp HTTP/1.1
```

### Example Response

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

## Start a Test

Start the currently loaded test profile. A profile must already be loaded via `/opentest`.

- **COM Method:** `StartTest()`

```http
POST /api/v1/starttest HTTP/1.1
Host: 127.0.0.1:5000
Accept: */*
Content-Length: 0
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

### Error: TEDS configuration not been read from hardware

If the profile requires TEDS and the TEDS data has not been read, the test will fail to start with a 500 error:

```json
{
  "error": {
    "description": "Exception occurred.",
    "details": "Failed loading input configuration",
    "source": "VibrationVIEW",
    "type": "com_error"
  },
  "success": false
}
```

See [TEDS.md](TEDS.md) for how to read and apply TEDS before starting a test.

## Run a Profile (Open + Start)

Open a profile and start it in a single operation. Supports the same GET/POST/PUT options as `/opentest`.

- **COM Method:** `RunTest(filepath)`

```http
GET /api/v1/runtest?filename=test1.vsp HTTP/1.1
Host: 127.0.0.1:5000
Accept: */*
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

The same TEDS-related error as `/starttest` can occur if the input configuration has not been loaded.
