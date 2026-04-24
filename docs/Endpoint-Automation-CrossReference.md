# VibrationVIEW REST API to COM Automation Cross-Reference

This document maps every REST API endpoint to its corresponding VibrationVIEW COM/Automation method, with descriptions from the official VibrationVIEW Automation Interface documentation.

All endpoints are prefixed with `/api/v1/`.

---

<details>
<summary><strong>Basic Control</strong> — <code>routes/basic_control.py</code></summary>

| REST Endpoint | COM Method | Automation Description |
|---|---|---|
| `/starttest` | `StartTest()` | Start currently loaded test |
| `/runtest` | `RunTest(filepath)` | Load and run test \<filename\> |
| `/stoptest` | `StopTest()` | Stop running test |
| `/resumetest` | `ResumeTest()` | Resume a paused, but previously running test |
| `/opentest` | `OpenTest(filepath)` | Load test \<filename\>, but don't start it |
| `/closetest` | `CloseTest(profile_name)` | Close a test profile by name |
| `/closetab` | `CloseTab(tab_index)` | Close a document tab by index |
| `/listopentests` | `ListOpenTests()` | Return a list of the names of the open test tabs |
| `/savedata` | `SaveData(filename)` | Save VibrationVIEW data file \<filename\> |
| `/testcom` | Multiple | *API-only composite* — calls `GetSoftwareVersion()`, `GetHardwareInputChannels()`, `GetHardwareOutputChannels()`, `GetHardwareSerialNumber()`, `IsReady()` |

</details>

<details>
<summary><strong>Status Properties</strong> — <code>routes/status_properties.py</code></summary>

| REST Endpoint | COM Method | Automation Description |
|---|---|---|
| `/status` | `Status()` | Get VibrationVIEW Status |
| `/isready` | `IsReady()` | True if the controller is booted and ready to accept a command |
| `/isrunning` | `Running` | Status flag, returns TRUE when the test is running (the output is live) |
| `/isstarting` | `Starting` | Status flag, returns TRUE at test startup, until the test reaches full level |
| `/ischanginglevel` | `ChangingLevel` | Status value, returns TRUE when the test is transitioning from one schedule level to another |
| `/isholdlevel` | `Hold Level` | True if schedule timer is in hold |
| `/isopenloop` | `OpenLoop` | Status value, returns TRUE when the OpenLoop check box is checked |
| `/isaborted` | `Aborted` | Status value, returns TRUE when test has aborted (any red stop code) |
| `/canresumetest` | `CanResumeTest` | Property is TRUE if test is in a state which allows resume |
| `/allstatus` | Multiple | *API-only composite* — returns all status properties in one call |

</details>

<details>
<summary><strong>Data Retrieval</strong> — <code>routes/data_retrieval.py</code></summary>

| REST Endpoint | COM Method | Automation Description |
|---|---|---|
| `/demand` | `Demand()` | Get the demand values for each loop |
| `/control` | `Control()` | Get the control values for each loop |
| `/channel` | `Channel()` | Get channel values |
| `/output` | `Output()` | Get the output values for each loop |
| `/channelunit` | `ChannelUnit(channelnum)` | Get the channel unit associated with ChannelNum |
| `/channellabel` | `ChannelLabel(channelnum)` | Channel Labels |
| `/controlunit` | `ControlUnit(loopnum)` | Get the control unit associated with LoopNum |
| `/controllabel` | `ControlLabel(loopnum)` | Control Label |
| `/getdatafile` | `ReportField('LastDataFile')` | *Uses ReportField to get path to the last data file* |

</details>

<details>
<summary><strong>Advanced Control</strong> — <code>routes/advanced_control.py</code></summary>

| REST Endpoint | COM Method | Automation Description |
|---|---|---|
| `/testtype` | `TestType()` / `TestType(value)` | Returns the current test type: 0=System Check, 1=Sine, 2=Random, 4=Shock, 6=FDR |

</details>

<details>
<summary><strong>Advanced Control — Sine</strong> — <code>routes/advanced_control_sine.py</code></summary>

| REST Endpoint | COM Method | Automation Description |
|---|---|---|
| `/sweepup` | `SweepUp()` | Change sweep direction to Up (Sine ONLY) |
| `/sweepdown` | `SweepDown()` | Change sweep direction to Down (Sine ONLY) |
| `/sweepstepup` | `SweepStepUp()` | Step the sine frequency up in 1Hz steps (Sine ONLY) |
| `/sweepstepdown` | `SweepStepDown()` | Step the sine frequency down in 1Hz steps (Sine ONLY) |
| `/sweephold` | `SweepHold()` | Stop sweep (Sine ONLY) |
| `/sweepresonancehold` | `SweepResonanceHold()` | Stop sweep and hold on resonance (Sine ONLY) |
| `/demandmultiplier` | `DemandMultiplier()` / `DemandMultiplier(value)` | Multiplier (in +/-dB) for Demand Output (Sine ONLY) |
| `/sweepmultiplier` | `SweepMultiplier()` / `SweepMultiplier(value)` | Add a multiplier factor (0.1x to 10x) to sweep rate (Sine ONLY) |
| `/sinefrequency` | `SineFrequency()` / `SineFrequency(value)` | Set or modify the sine frequency |

</details>

<details>
<summary><strong>Advanced Control — System Check</strong> — <code>routes/advanced_control_system_check.py</code></summary>

| REST Endpoint | COM Method | Automation Description |
|---|---|---|
| `/systemcheckfrequency` | `SystemCheckFrequency()` / `SystemCheckFrequency(value)` | Property to get/set the frequency (System Check ONLY) |
| `/systemcheckoutputvoltage` | `SystemCheckOutputVoltage()` / `SystemCheckOutputVoltage(value)` | Property to get/set the voltage (System Check ONLY) |

</details>

<details>
<summary><strong>GUI Control</strong> — <code>routes/gui_control.py</code></summary>

| REST Endpoint | COM Method | Automation Description |
|---|---|---|
| `/edittest` | `EditTest(szTestName)` | Edit specified test file |
| `/abortedit` | `AbortEdit()` | Abort edit previously started with Edit Test |
| `/minimize` | `Minimize()` | Minimize VibrationVIEW window |
| `/restore` | `Restore()` | Restore VibrationVIEW |
| `/maximize` | `Maximize()` | Maximize VibrationVIEW Window |
| `/activate` | `Activate()` | Activate VibrationVIEW |

</details>

<details>
<summary><strong>Hardware Config</strong> — <code>routes/hardware_config.py</code></summary>

| REST Endpoint | COM Method | Automation Description |
|---|---|---|
| `/gethardwareinputchannels` | `HardwareInputChannels` | Connected hardware maximum input channels |
| `/gethardwareoutputchannels` | `HardwareOutputChannels` | Connected hardware maximum output channels |
| `/gethardwareserialnumber` | `HardwareSerialNumber` | Connected hardware Serial Number |
| `/getsoftwareversion` | `SoftwareVersion` | Get the VibrationVIEW software version |
| `/hardwaresupportscapacitorcoupled` | `HardwareSupportsCapacitorCoupled(channel)` | Connected hardware supports Capacitor Coupled inputs |
| `/hardwaresupportsaccelpowersource` | `HardwareSupportsAccelPowerSource(channel)` | Connected hardware supports IEPE inputs |
| `/hardwaresupportsdifferential` | `HardwareSupportsDifferential(channel)` | Connected hardware supports Differential inputs |

</details>

<details>
<summary><strong>Input Configuration</strong> — <code>routes/input_config.py</code></summary>

| REST Endpoint | COM Method | Automation Description |
|---|---|---|
| `/inputcaldate` | `InputCalDate(channel)` | Input transducer Calibration Date |
| `/inputserialnumber` | `InputSerialNumber(channel)` | Input transducer serial number |
| `/inputsensitivity` | `InputSensitivity(channel)` | Input transducer sensitivity |
| `/inputengineeringscale` | `InputEngineeringScale(channel)` | Input transducer Engineering unit scale to metric unit |
| `/inputcapacitorcoupled` | `InputCapacitorCoupled(channel)` / `InputCapacitorCoupled(channel, value)` | Input transducer capacitor coupled |
| `/inputaccelpowersource` | `InputAccelPowerSource(channel)` / `InputAccelPowerSource(channel, value)` | Input transducer IEPE |
| `/inputdifferential` | `InputDifferential(channel)` / `InputDifferential(channel, value)` | Input transducer differential mode |
| `/inputmode` | `InputMode(channel, powerSource, capCoupled, differential)` | Input transducer channel mode |
| `/inputcalibration` | `InputCalibration(channel, sensitivity, serialnumber, caldate)` | Input transducer calibration information |
| `/inputconfigurationfile` | `set_InputConfigurationFile(filename)` | Loads the Input Configuration .vic file into VibrationVIEW |
| `/ischanneldifferentdatabase` | `IsChannelDifferentThanDatabase(channel)` | Check if channel config differs from transducer database |
| `/channeldatabaseids` | `ChannelDatabaseIDs(channel)` | Get transducer database IDs for a channel |
| `/updatechannelconfigfromdatabase` | `UpdateChannelConfigFromDatabase(channel)` | Update channel config from transducer database |
| `/transducerdatabaserecord` | `TransducerDatabaseRecord(guid)` | Get transducer database record by GUID |

</details>

<details>
<summary><strong>Recording</strong> — <code>routes/recording.py</code></summary>

| REST Endpoint | COM Method | Automation Description |
|---|---|---|
| `/recordstart` | `RecordStart()` | Start the data recorder |
| `/recordstop` | `RecordStop()` | Stop the data recorder |
| `/recordpause` | `RecordPause()` | Pause the data recorder |
| `/recordgetfilename` | `RecordGetFilename()` | Get the file name of the last recording |
| `/testrecording` | `RecordGetFilename()` | *API-only test endpoint* — verifies recording COM connection |

</details>

<details>
<summary><strong>Reporting</strong> — <code>routes/reporting.py</code></summary>

| REST Endpoint | COM Method | Automation Description |
|---|---|---|
| `/reportfield` | `ReportField(sField)` | Pass request report template, returns filled in value |
| `/reportfields` | `ReportFields(fields)` | Get multiple report fields at once |
| `/reportfieldshistory` | `ReportFieldsHistory(fields)` | Get report field names and values from history files |
| `/reportvector` | `ReportVector(vectors, array_out)` | Get report vector data |
| `/reportvectorheader` | `ReportVectorHeader(vectors, array_out)` | Get report vector header information |
| `/reportvectorhistory` | `ReportVectorHistory(vectors, array_out)` | Get report vector data from history files for most recently run test |
| `/formfields` | `FormFields()` | Get array of all form field values |
| `/formfields` | `PostFormFields(fields)` | Post array of form field values |

</details>

<details>
<summary><strong>Report Generation</strong> — <code>routes/report_generation.py</code></summary>

| REST Endpoint | COM Method | Automation Description |
|---|---|---|
| `/generatereport` | `GenerateReportFromVV(filePath, templateName, outputName)` | *Library function* — generates a report file from VibrationVIEW data using a template |
| `/generatetxt` | `GenerateTXTFromVV(filePath, outputName)` | *Library function* — converts VibrationVIEW data to text format |
| `/generateuff` | `GenerateUFFFromVV(filePath, outputName)` | *Library function* — converts VibrationVIEW data to Universal File Format |
| `/datafile` | `ReportField('LastDataFile')` | *Uses ReportField to locate and return raw .vrd data file* |
| `/datafiles` | `ReportFieldsHistory('LastData,...')` | *Uses ReportFieldsHistory to return all data files as zip archive* |

</details>

<details>
<summary><strong>Auxiliary Inputs</strong> — <code>routes/aux_inputs.py</code></summary>

| REST Endpoint | COM Method | Automation Description |
|---|---|---|
| `/rearinput` | `RearInput()` | Get Rear Input Vector Array |
| `/rearinputunit` | `RearInputUnit(channel)` | Get Units for Rear Input Data |
| `/rearinputlabel` | `RearInputLabel(channel)` | Get Label for Rear Input Data |

</details>

<details>
<summary><strong>TEDS</strong> — <code>routes/teds.py</code></summary>

| REST Endpoint | COM Method | Automation Description |
|---|---|---|
| `/inputteds` | `Teds(channel)` for all channels | Returns TEDS values for all channels |
| `/inputtedschannel` | `Teds(channel)` | Returns TEDS values for requested channel |
| `/teds` | `Teds(channel)` / `Teds()` | Returns TEDS values for requested channel |
| `/tedsreadandapply` | `TedsReadAndApply()` | Read TEDS from hardware and apply to channels |
| `/tedsverifyandapply` | `TedsVerifyAndApply(urns)` | Verify TEDS data and apply to channels |
| `/tedsread` | `TedsRead()` + `TedsFromURN(urn)` | Read TEDS from hardware; Get TEDS data from a URN |

</details>

<details>
<summary><strong>Vectors (Legacy)</strong> — <code>routes/vectors_legacy.py</code></summary>

| REST Endpoint | COM Method | Automation Description |
|---|---|---|
| `/vector` | `Vector(vectorenum, columns)` | Get Raw Data |
| `/vectorunit` | `VectorUnit(vectorenum)` | Get Units for Raw Data |
| `/vectorlabel` | `VectorLabel(vectorenum)` | Get Label for Raw Data |
| `/vectorlength` | `VectorLength(vectorenum)` | Required array length for Raw Data Vector Array |

</details>

<details>
<summary><strong>Virtual Channels</strong> — <code>routes/virtual_channels.py</code></summary>

| REST Endpoint | COM Method | Automation Description |
|---|---|---|
| `/removeallvirtualchannels` | `RemoveAllVirtualChannels()` | Remove all virtual channels |
| `/importvirtualchannels` | `ImportVirtualChannels(filepath)` | Import virtual channels from a file |

</details>

<details>
<summary><strong>Event Log</strong> — <code>routes/log.py</code></summary>

| REST Endpoint | COM Method | Automation Description |
|---|---|---|
| `/log` | `ReportField('Events')` | *Uses ReportField with 'Events' parameter to retrieve the event log* |

</details>
