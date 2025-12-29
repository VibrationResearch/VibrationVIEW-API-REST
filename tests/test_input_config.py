# ============================================================================
# FILE: tests/test_input_config.py
# ============================================================================

"""
Tests for input configuration routes
"""

import json
from app import set_vv_instance, reset_vv_instance
from tests.mocks.mock_vibrationviewapi import MockVibrationVIEW


class TestInputConfig:
    def setup_method(self):
        """Setup for each test method"""
        reset_vv_instance()
        self.mock_instance = MockVibrationVIEW()
        set_vv_instance(self.mock_instance)

    def teardown_method(self):
        """Cleanup after each test method"""
        reset_vv_instance()

    # -------------------------------------------------------------------------
    # InputMode tests - JSON body
    # -------------------------------------------------------------------------
    def test_inputmode_json_success(self, client):
        """Test POST /inputmode with JSON body"""
        response = client.post(
            "/api/v1/inputmode",
            json={
                "channel": 1,
                "powersource": True,
                "capcoupled": False,
                "differential": True
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] is True
        assert data["data"]["channel"] == 1
        assert data["data"]["powersource"] is True
        assert data["data"]["capcoupled"] is False
        assert data["data"]["differential"] is True

        # Verify the COM method was called with correct parameters
        # Channel 1 (user) -> Channel 0 (COM, 0-based)
        self.mock_instance.InputMode.assert_called_once_with(0, True, False, True)

    def test_inputmode_channel_conversion(self, client):
        """Test that channel numbers are converted from 1-based to 0-based"""
        response = client.post(
            "/api/v1/inputmode",
            json={
                "channel": 4,
                "powersource": False,
                "capcoupled": True,
                "differential": False
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["channel"] == 4

        # Verify COM method called with 0-based index (channel 4 -> index 3)
        self.mock_instance.InputMode.assert_called_once_with(3, False, True, False)

    # -------------------------------------------------------------------------
    # InputMode tests - Query parameters
    # -------------------------------------------------------------------------
    def test_inputmode_query_params_get(self, client):
        """Test GET /inputmode with query parameters"""
        response = client.get(
            "/api/v1/inputmode?channel=1&powersource=true&capcoupled=false&differential=false"
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] is True
        assert data["data"]["channel"] == 1
        assert data["data"]["powersource"] is True
        assert data["data"]["capcoupled"] is False
        assert data["data"]["differential"] is False

        # Verify the COM method was called with correct parameters
        self.mock_instance.InputMode.assert_called_once_with(0, True, False, False)

    def test_inputmode_query_params_post(self, client):
        """Test POST /inputmode with query parameters"""
        response = client.post(
            "/api/v1/inputmode?channel=2&powersource=false&capcoupled=true&differential=true"
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["channel"] == 2
        assert data["data"]["powersource"] is False
        assert data["data"]["capcoupled"] is True
        assert data["data"]["differential"] is True

        # Verify COM method called with 0-based index (channel 2 -> index 1)
        self.mock_instance.InputMode.assert_called_once_with(1, False, True, True)

    def test_inputmode_query_params_all_false(self, client):
        """Test GET /inputmode with all boolean parameters as false strings"""
        response = client.get(
            "/api/v1/inputmode?channel=1&powersource=false&capcoupled=false&differential=false"
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["powersource"] is False
        assert data["data"]["capcoupled"] is False
        assert data["data"]["differential"] is False

        self.mock_instance.InputMode.assert_called_once_with(0, False, False, False)

    def test_inputmode_query_params_all_true(self, client):
        """Test GET /inputmode with all boolean parameters as true strings"""
        response = client.get(
            "/api/v1/inputmode?channel=1&powersource=true&capcoupled=true&differential=true"
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["powersource"] is True
        assert data["data"]["capcoupled"] is True
        assert data["data"]["differential"] is True

        self.mock_instance.InputMode.assert_called_once_with(0, True, True, True)

    # -------------------------------------------------------------------------
    # InputMode tests - Error cases
    # -------------------------------------------------------------------------
    def test_inputmode_missing_channel(self, client):
        """Test POST /inputmode without channel parameter"""
        response = client.post(
            "/api/v1/inputmode",
            json={
                "powersource": True,
                "capcoupled": False,
                "differential": True
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "channel" in data["error"]["message"].lower()

    def test_inputmode_missing_powersource(self, client):
        """Test POST /inputmode without powersource parameter"""
        response = client.post(
            "/api/v1/inputmode",
            json={
                "channel": 1,
                "capcoupled": False,
                "differential": True
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "powersource" in data["error"]["message"].lower()

    def test_inputmode_missing_capcoupled(self, client):
        """Test POST /inputmode without capcoupled parameter"""
        response = client.post(
            "/api/v1/inputmode",
            json={
                "channel": 1,
                "powersource": True,
                "differential": True
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "capcoupled" in data["error"]["message"].lower()

    def test_inputmode_missing_differential(self, client):
        """Test POST /inputmode without differential parameter"""
        response = client.post(
            "/api/v1/inputmode",
            json={
                "channel": 1,
                "powersource": True,
                "capcoupled": False
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "differential" in data["error"]["message"].lower()

    def test_inputmode_missing_params(self, client):
        """Test POST /inputmode without any parameters"""
        response = client.post("/api/v1/inputmode")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "missing" in data["error"]["message"].lower()

    def test_inputmode_invalid_channel_zero(self, client):
        """Test POST /inputmode with channel 0 (invalid, 1-based)"""
        response = client.post(
            "/api/v1/inputmode",
            json={
                "channel": 0,
                "powersource": True,
                "capcoupled": False,
                "differential": True
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False

    def test_inputmode_query_params_missing_channel(self, client):
        """Test GET /inputmode with missing channel in query params"""
        response = client.get(
            "/api/v1/inputmode?powersource=true&capcoupled=false&differential=false"
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "channel" in data["error"]["message"].lower()

    # -------------------------------------------------------------------------
    # Input Channel Properties tests
    # -------------------------------------------------------------------------
    def test_inputcaldate_success(self, client):
        """Test GET /inputcaldate with valid channel"""
        self.mock_instance.InputCalDate.return_value = "2025-01-15"

        response = client.get("/api/v1/inputcaldate?1")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] == "2025-01-15"
        assert data["data"]["channel"] == 1
        # Channel 1 (user) -> Channel 0 (COM)
        self.mock_instance.InputCalDate.assert_called_once_with(0)

    def test_inputcaldate_missing_channel(self, client):
        """Test GET /inputcaldate without channel"""
        response = client.get("/api/v1/inputcaldate")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_PARAMETER"

    def test_inputcaldate_invalid_channel(self, client):
        """Test GET /inputcaldate with invalid channel"""
        response = client.get("/api/v1/inputcaldate?0")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False

    def test_inputserialnumber_success(self, client):
        """Test GET /inputserialnumber with valid channel"""
        self.mock_instance.InputSerialNumber.return_value = "SN-12345"

        response = client.get("/api/v1/inputserialnumber?1")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] == "SN-12345"
        assert data["data"]["channel"] == 1
        self.mock_instance.InputSerialNumber.assert_called_once_with(0)

    def test_inputserialnumber_missing_channel(self, client):
        """Test GET /inputserialnumber without channel"""
        response = client.get("/api/v1/inputserialnumber")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False

    def test_inputsensitivity_success(self, client):
        """Test GET /inputsensitivity with valid channel"""
        self.mock_instance.InputSensitivity.return_value = 10.0

        response = client.get("/api/v1/inputsensitivity?1")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] == 10.0
        assert data["data"]["channel"] == 1
        self.mock_instance.InputSensitivity.assert_called_once_with(0)

    def test_inputsensitivity_missing_channel(self, client):
        """Test GET /inputsensitivity without channel"""
        response = client.get("/api/v1/inputsensitivity")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False

    def test_inputengineeringscale_success(self, client):
        """Test GET /inputengineeringscale with valid channel"""
        self.mock_instance.InputEngineeringScale.return_value = 1.0

        response = client.get("/api/v1/inputengineeringscale?1")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] == 1.0
        assert data["data"]["channel"] == 1
        self.mock_instance.InputEngineeringScale.assert_called_once_with(0)

    def test_inputengineeringscale_missing_channel(self, client):
        """Test GET /inputengineeringscale without channel"""
        response = client.get("/api/v1/inputengineeringscale")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False

    # -------------------------------------------------------------------------
    # Input Channel Settings (Get/Set) tests
    # -------------------------------------------------------------------------
    def test_inputcapacitorcoupled_get(self, client):
        """Test GET /inputcapacitorcoupled"""
        self.mock_instance.InputCapacitorCoupled.return_value = True

        response = client.get("/api/v1/inputcapacitorcoupled?1")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] is True
        assert data["data"]["channel"] == 1
        self.mock_instance.InputCapacitorCoupled.assert_called_once_with(0)

    def test_inputcapacitorcoupled_post_set_true(self, client):
        """Test POST /inputcapacitorcoupled to set value to true"""
        self.mock_instance.InputCapacitorCoupled.return_value = True

        response = client.post("/api/v1/inputcapacitorcoupled?1&true")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["value_set"] is True
        self.mock_instance.InputCapacitorCoupled.assert_called_once_with(0, True)

    def test_inputcapacitorcoupled_post_set_false(self, client):
        """Test POST /inputcapacitorcoupled to set value to false"""
        self.mock_instance.InputCapacitorCoupled.return_value = False

        response = client.post("/api/v1/inputcapacitorcoupled?1&false")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["value_set"] is False
        self.mock_instance.InputCapacitorCoupled.assert_called_once_with(0, False)

    def test_inputcapacitorcoupled_missing_channel(self, client):
        """Test GET /inputcapacitorcoupled without channel"""
        response = client.get("/api/v1/inputcapacitorcoupled")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False

    def test_inputaccelpowersource_get(self, client):
        """Test GET /inputaccelpowersource"""
        self.mock_instance.InputAccelPowerSource.return_value = True

        response = client.get("/api/v1/inputaccelpowersource?1")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] is True
        self.mock_instance.InputAccelPowerSource.assert_called_once_with(0)

    def test_inputaccelpowersource_post_set(self, client):
        """Test POST /inputaccelpowersource to set value"""
        self.mock_instance.InputAccelPowerSource.return_value = False

        response = client.post("/api/v1/inputaccelpowersource?1&false")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["value_set"] is False
        self.mock_instance.InputAccelPowerSource.assert_called_once_with(0, False)

    def test_inputaccelpowersource_missing_channel(self, client):
        """Test GET /inputaccelpowersource without channel"""
        response = client.get("/api/v1/inputaccelpowersource")

        assert response.status_code == 400

    def test_inputdifferential_get(self, client):
        """Test GET /inputdifferential"""
        self.mock_instance.InputDifferential.return_value = False

        response = client.get("/api/v1/inputdifferential?1")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] is False
        self.mock_instance.InputDifferential.assert_called_once_with(0)

    def test_inputdifferential_post_set(self, client):
        """Test POST /inputdifferential to set value"""
        self.mock_instance.InputDifferential.return_value = True

        response = client.post("/api/v1/inputdifferential?1&true")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["value_set"] is True
        self.mock_instance.InputDifferential.assert_called_once_with(0, True)

    def test_inputdifferential_missing_channel(self, client):
        """Test GET /inputdifferential without channel"""
        response = client.get("/api/v1/inputdifferential")

        assert response.status_code == 400

    # -------------------------------------------------------------------------
    # InputCalibration tests
    # -------------------------------------------------------------------------
    def test_inputcalibration_query_params(self, client):
        """Test GET /inputcalibration with query params"""
        self.mock_instance.InputCalibration.return_value = True

        response = client.get(
            "/api/v1/inputcalibration?channel=1&sensitivity=100.5&serialnumber=SN123&caldate=2025-01-15"
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] is True
        assert data["data"]["channel"] == 1
        assert data["data"]["sensitivity"] == 100.5
        assert data["data"]["serialnumber"] == "SN123"
        assert data["data"]["caldate"] == "2025-01-15"
        self.mock_instance.InputCalibration.assert_called_once_with(0, 100.5, "SN123", "2025-01-15")

    def test_inputcalibration_json_body(self, client):
        """Test POST /inputcalibration with JSON body"""
        self.mock_instance.InputCalibration.return_value = True

        response = client.post(
            "/api/v1/inputcalibration",
            json={
                "channel": 2,
                "sensitivity": 50.0,
                "serialnumber": "SN456",
                "caldate": "2025-06-01"
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["channel"] == 2
        # Channel 2 -> index 1
        self.mock_instance.InputCalibration.assert_called_once_with(1, 50.0, "SN456", "2025-06-01")

    def test_inputcalibration_missing_params(self, client):
        """Test POST /inputcalibration with missing parameters"""
        response = client.post(
            "/api/v1/inputcalibration",
            json={"channel": 1, "sensitivity": 100}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "serialnumber" in data["error"]["message"].lower() or "caldate" in data["error"]["message"].lower()

    def test_inputcalibration_invalid_sensitivity(self, client):
        """Test POST /inputcalibration with invalid sensitivity"""
        response = client.post(
            "/api/v1/inputcalibration",
            json={
                "channel": 1,
                "sensitivity": "invalid",
                "serialnumber": "SN123",
                "caldate": "2025-01-15"
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "sensitivity" in data["error"]["message"].lower()

    # -------------------------------------------------------------------------
    # InputConfigurationFile tests
    # -------------------------------------------------------------------------
    def test_inputconfigurationfile_get(self, client):
        """Test GET /inputconfigurationfile"""
        self.mock_instance.GetInputConfigurationFile = lambda: "10mv per G.vic"

        response = client.get("/api/v1/inputconfigurationfile")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] == "10mv per G.vic"

    def test_inputconfigurationfile_post_load_existing(self, client):
        """Test POST /inputconfigurationfile to load existing file by name"""
        self.mock_instance.SetInputConfigurationFile = lambda path: None

        response = client.post("/api/v1/inputconfigurationfile?filename=10mv per G.vic")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "10mv per G.vic" in data["data"]["filepath"]

    def test_inputconfigurationfile_post_missing_filename(self, client):
        """Test POST /inputconfigurationfile without filename"""
        response = client.post("/api/v1/inputconfigurationfile")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False

    # -------------------------------------------------------------------------
    # Transducer Database tests
    # -------------------------------------------------------------------------
    def test_ischanneldifferentdatabase_true(self, client):
        """Test GET /ischanneldifferentdatabase when channel differs"""
        self.mock_instance.IsChannelDifferentThanDatabase = lambda ch: True

        response = client.get("/api/v1/ischanneldifferentdatabase?1")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] is True
        assert data["data"]["channel"] == 1
        assert "differs" in data["message"]

    def test_ischanneldifferentdatabase_false(self, client):
        """Test GET /ischanneldifferentdatabase when channel matches"""
        self.mock_instance.IsChannelDifferentThanDatabase = lambda ch: False

        response = client.get("/api/v1/ischanneldifferentdatabase?1")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] is False
        assert "matches" in data["message"]

    def test_ischanneldifferentdatabase_missing_channel(self, client):
        """Test GET /ischanneldifferentdatabase without channel"""
        response = client.get("/api/v1/ischanneldifferentdatabase")

        assert response.status_code == 400

    def test_channeldatabaseids_success(self, client):
        """Test GET /channeldatabaseids"""
        mock_ids = ["guid-123", "guid-456"]
        self.mock_instance.ChannelDatabaseIDs = lambda ch: mock_ids

        response = client.get("/api/v1/channeldatabaseids?1")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] == mock_ids
        assert data["data"]["channel"] == 1

    def test_channeldatabaseids_missing_channel(self, client):
        """Test GET /channeldatabaseids without channel"""
        response = client.get("/api/v1/channeldatabaseids")

        assert response.status_code == 400

    def test_updatechannelconfigfromdatabase_success(self, client):
        """Test POST /updatechannelconfigfromdatabase"""
        self.mock_instance.UpdateChannelConfigFromDatabase = lambda ch: True

        response = client.post("/api/v1/updatechannelconfigfromdatabase?1")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] is True
        assert data["data"]["channel"] == 1
        assert "updated" in data["message"]

    def test_updatechannelconfigfromdatabase_get(self, client):
        """Test GET /updatechannelconfigfromdatabase (also supported)"""
        self.mock_instance.UpdateChannelConfigFromDatabase = lambda ch: True

        response = client.get("/api/v1/updatechannelconfigfromdatabase?1")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

    def test_updatechannelconfigfromdatabase_missing_channel(self, client):
        """Test POST /updatechannelconfigfromdatabase without channel"""
        response = client.post("/api/v1/updatechannelconfigfromdatabase")

        assert response.status_code == 400

    def test_transducerdatabaserecord_success(self, client):
        """Test GET /transducerdatabaserecord"""
        mock_record = ["Manufacturer", "Model", "SN123", "100.0", "mV/g"]
        self.mock_instance.TransducerDatabaseRecord = lambda guid: mock_record

        response = client.get("/api/v1/transducerdatabaserecord?guid=abc-123-def")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] == mock_record
        assert data["data"]["guid"] == "abc-123-def"

    def test_transducerdatabaserecord_missing_guid(self, client):
        """Test GET /transducerdatabaserecord without guid"""
        response = client.get("/api/v1/transducerdatabaserecord")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "guid" in data["error"]["message"].lower()
