"""Tests for VeSync binary sensor platform."""

from unittest.mock import MagicMock

import pytest

from homeassistant.helpers.entity import EntityCategory

from custom_components.vesync.binary_sensor import (
    VeSyncFilterOpenStateSensor,
    VeSyncOutOfWaterSensor,
    VeSyncWaterTankLiftedSensor,
    VeSyncairfryerSensor,
)
from custom_components.vesync.const import BINARY_SENSOR_TYPES_AIRFRYER


# ---------------------------------------------------------------------------
# Humidifier binary sensor tests
# ---------------------------------------------------------------------------


class TestVeSyncOutOfWaterSensor:
    """Tests for VeSyncOutOfWaterSensor."""

    @pytest.fixture
    def water_sensor(self, mock_humidifier_device, mock_coordinator):
        """Return an out-of-water sensor entity."""
        return VeSyncOutOfWaterSensor(mock_humidifier_device, mock_coordinator)

    def test_unique_id_suffix(self, water_sensor):
        """Append -out_of_water to unique_id."""
        assert water_sensor.unique_id.endswith("-out_of_water")

    def test_name_suffix(self, water_sensor):
        """Append 'out of water' to name."""
        assert "out of water" in water_sensor.name

    def test_is_on_true(self, water_sensor, mock_humidifier_device):
        """Return True when water_lacks is True."""
        mock_humidifier_device.state.water_lacks = True
        assert water_sensor.is_on is True

    def test_is_on_false(self, water_sensor, mock_humidifier_device):
        """Return False when water_lacks is False."""
        mock_humidifier_device.state.water_lacks = False
        assert water_sensor.is_on is False

    def test_entity_category(self, water_sensor):
        """Return DIAGNOSTIC entity category."""
        assert water_sensor.entity_category == EntityCategory.DIAGNOSTIC


class TestVeSyncWaterTankLiftedSensor:
    """Tests for VeSyncWaterTankLiftedSensor."""

    @pytest.fixture
    def tank_sensor(self, mock_humidifier_device, mock_coordinator):
        """Return a water tank lifted sensor entity."""
        return VeSyncWaterTankLiftedSensor(mock_humidifier_device, mock_coordinator)

    def test_unique_id_suffix(self, tank_sensor):
        """Append -water_tank_lifted to unique_id."""
        assert tank_sensor.unique_id.endswith("-water_tank_lifted")

    def test_is_on(self, tank_sensor, mock_humidifier_device):
        """Return water_tank_lifted from device state."""
        mock_humidifier_device.state.water_tank_lifted = True
        assert tank_sensor.is_on is True


class TestVeSyncFilterOpenStateSensor:
    """Tests for VeSyncFilterOpenStateSensor."""

    @pytest.fixture
    def filter_device(self, mock_coordinator):
        """Return a device with filter_open_state."""
        device = MagicMock()
        device.cid = "filter-cid"
        device.sub_device_no = None
        device.device_name = "Purifier"
        device.device_type = "LAP-C201S"
        device.connection_status = "online"
        device.current_firm_version = "1.0"
        state = MagicMock(spec=[])
        state.filter_open_state = True
        device.state = state
        return device

    @pytest.fixture
    def filter_sensor(self, filter_device, mock_coordinator):
        """Return a filter open state sensor entity."""
        return VeSyncFilterOpenStateSensor(filter_device, mock_coordinator)

    def test_unique_id_suffix(self, filter_sensor):
        """Append -filter-open-state to unique_id."""
        assert filter_sensor.unique_id.endswith("-filter-open-state")

    def test_is_on(self, filter_sensor, filter_device):
        """Return filter_open_state from device state."""
        assert filter_sensor.is_on is True


# ---------------------------------------------------------------------------
# Airfryer binary sensor tests
# ---------------------------------------------------------------------------


class TestVeSyncAirfryerBinarySensor:
    """Tests for VeSyncairfryerSensor (binary)."""

    @pytest.fixture
    def heating_sensor(self, mock_airfryer_device, mock_coordinator):
        """Return an airfryer is_heating binary sensor."""
        stype = BINARY_SENSOR_TYPES_AIRFRYER["is_heating"]
        return VeSyncairfryerSensor(mock_airfryer_device, mock_coordinator, stype)

    def test_unique_id_suffix(self, heating_sensor):
        """Include sensor type in unique_id."""
        assert "is_heating" in heating_sensor.unique_id

    def test_name(self, heating_sensor):
        """Return the sensor type name."""
        assert heating_sensor.name == "preheating"

    def test_is_on(self, heating_sensor, mock_airfryer_device):
        """Return is_heating attribute from device."""
        assert heating_sensor.is_on is True

    def test_icon(self, heating_sensor):
        """Return the correct icon."""
        assert heating_sensor.icon == "mdi:pot-steam-outline"

    def test_entity_category(self, heating_sensor):
        """Return DIAGNOSTIC entity category."""
        assert heating_sensor.entity_category == EntityCategory.DIAGNOSTIC
