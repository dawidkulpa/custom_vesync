"""Tests for common utilities and base entity classes."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.vesync.common import (
    VeSyncBaseEntity,
    VeSyncDevice,
    async_process_devices,
    has_feature,
)
from custom_components.vesync.const import (
    VS_BINARY_SENSORS,
    VS_BUTTON,
    VS_FANS,
    VS_HUMIDIFIERS,
    VS_LIGHTS,
    VS_NUMBERS,
    VS_SENSORS,
    VS_SWITCHES,
)

from .conftest import _make_manager_devices, _make_state


# ---------------------------------------------------------------------------
# has_feature tests
# ---------------------------------------------------------------------------


class TestHasFeature:
    """Tests for the has_feature helper."""

    def test_returns_true_when_attribute_exists(self):
        """Return True when the attribute exists on device.state."""
        device = MagicMock()
        device.state = MagicMock()
        device.state.humidity = 55
        assert has_feature(device, "humidity") is True

    def test_returns_false_when_attribute_missing(self):
        """Return False when the attribute is absent."""
        device = MagicMock()
        device.state = MagicMock(spec=[])
        assert has_feature(device, "air_quality") is False

    def test_returns_false_when_attribute_is_none(self):
        """Return False when the attribute value is None."""
        device = MagicMock()
        device.state = MagicMock()
        device.state.humidity = None
        assert has_feature(device, "humidity") is False

    def test_returns_false_when_state_missing(self):
        """Return False when the state attribute does not exist on device."""
        device = MagicMock(spec=[])
        assert has_feature(device, "humidity") is False

    def test_returns_true_for_zero_value(self):
        """Return True when the attribute exists but is zero."""
        device = MagicMock()
        device.state = MagicMock()
        device.state.mist_level = 0
        assert has_feature(device, "mist_level") is True

    def test_returns_true_for_empty_string(self):
        """Return True when the attribute exists but is an empty string."""
        device = MagicMock()
        device.state = MagicMock()
        device.state.mode = ""
        assert has_feature(device, "mode") is True


# ---------------------------------------------------------------------------
# async_process_devices tests
# ---------------------------------------------------------------------------


class TestAsyncProcessDevices:
    """Tests for async_process_devices."""

    async def test_outlets_sorted_to_switches_and_sensors(
        self, hass, mock_outlet_device
    ):
        """Route outlets to switches and sensors platforms."""
        manager = MagicMock()
        manager.devices = _make_manager_devices(
            outlets=[mock_outlet_device],
        )

        result = await async_process_devices(hass, manager)

        assert mock_outlet_device in result[VS_SWITCHES]
        assert mock_outlet_device in result[VS_SENSORS]
        assert mock_outlet_device not in result[VS_FANS]
        assert mock_outlet_device not in result[VS_HUMIDIFIERS]

    async def test_bulbs_sorted_to_lights(
        self, hass, mock_bulb_dimmable_device
    ):
        """Route bulbs to lights platform."""
        manager = MagicMock()
        manager.devices = _make_manager_devices(
            bulbs=[mock_bulb_dimmable_device],
        )

        result = await async_process_devices(hass, manager)

        assert mock_bulb_dimmable_device in result[VS_LIGHTS]

    async def test_non_dimmable_switch_sorted_to_switches(
        self, hass, mock_wall_switch_device
    ):
        """Route non-dimmable wall switches to switches platform."""
        manager = MagicMock()
        manager.devices = _make_manager_devices(
            switches=[mock_wall_switch_device],
        )

        result = await async_process_devices(hass, manager)

        assert mock_wall_switch_device in result[VS_SWITCHES]
        assert mock_wall_switch_device not in result[VS_LIGHTS]

    async def test_dimmable_switch_sorted_to_lights(
        self, hass, mock_dimmer_device
    ):
        """Route dimmable wall switches to lights platform."""
        manager = MagicMock()
        manager.devices = _make_manager_devices(
            switches=[mock_dimmer_device],
        )

        result = await async_process_devices(hass, manager)

        assert mock_dimmer_device in result[VS_LIGHTS]
        assert mock_dimmer_device not in result[VS_SWITCHES]

    async def test_fan_sorted_to_fans(
        self, hass, mock_fan_device
    ):
        """Route VeSync fans to fans platform."""
        manager = MagicMock()
        manager.devices = _make_manager_devices(
            fans=[mock_fan_device],
        )

        result = await async_process_devices(hass, manager)

        assert mock_fan_device in result[VS_FANS]
        # Fans also get numbers, switches, sensors, binary_sensors, lights
        assert mock_fan_device in result[VS_NUMBERS]
        assert mock_fan_device in result[VS_SWITCHES]
        assert mock_fan_device in result[VS_SENSORS]
        assert mock_fan_device in result[VS_BINARY_SENSORS]
        assert mock_fan_device in result[VS_LIGHTS]

    async def test_humidifier_sorted_to_humidifiers(
        self, hass, mock_humidifier_device
    ):
        """Route VeSync humidifiers to humidifiers platform."""
        manager = MagicMock()
        manager.devices = _make_manager_devices(
            humidifiers=[mock_humidifier_device],
        )

        result = await async_process_devices(hass, manager)

        assert mock_humidifier_device in result[VS_HUMIDIFIERS]
        assert mock_humidifier_device not in result[VS_FANS]

    async def test_airfryer_sorted_correctly(
        self, hass, mock_airfryer_device
    ):
        """Route air fryers to sensors, binary_sensors, switches, and buttons."""
        manager = MagicMock()
        manager.devices = _make_manager_devices(
            air_fryers=[mock_airfryer_device],
        )

        result = await async_process_devices(hass, manager)

        assert mock_airfryer_device in result[VS_SENSORS]
        assert mock_airfryer_device in result[VS_BINARY_SENSORS]
        assert mock_airfryer_device in result[VS_SWITCHES]
        assert mock_airfryer_device in result[VS_BUTTON]

    async def test_empty_manager_returns_empty_device_dict(
        self, hass, mock_empty_manager
    ):
        """Return empty lists when manager has no devices."""
        result = await async_process_devices(hass, mock_empty_manager)

        for platform_list in result.values():
            assert platform_list == []


# ---------------------------------------------------------------------------
# VeSyncBaseEntity tests
# ---------------------------------------------------------------------------


class TestVeSyncBaseEntity:
    """Tests for VeSyncBaseEntity."""

    def test_unique_id_without_sub_device(self, mock_outlet_device, mock_coordinator):
        """Return cid as unique_id when sub_device_no is not an int."""
        mock_outlet_device.sub_device_no = None
        entity = VeSyncBaseEntity(mock_outlet_device, mock_coordinator)
        assert entity.unique_id == "outlet-cid"

    def test_unique_id_with_sub_device(self, mock_outlet_device, mock_coordinator):
        """Return cid + sub_device_no as unique_id."""
        mock_outlet_device.sub_device_no = 1
        entity = VeSyncBaseEntity(mock_outlet_device, mock_coordinator)
        assert entity.unique_id == "outlet-cid1"

    def test_name_returns_device_name(self, mock_outlet_device, mock_coordinator):
        """Return device_name as entity name."""
        entity = VeSyncBaseEntity(mock_outlet_device, mock_coordinator)
        assert entity.name == "TestOutlet"

    def test_available_when_online(self, mock_outlet_device, mock_coordinator):
        """Return True when device connection_status is online."""
        mock_outlet_device.state.connection_status = "online"
        entity = VeSyncBaseEntity(mock_outlet_device, mock_coordinator)
        assert entity.available is True

    def test_unavailable_when_offline(self, mock_outlet_device, mock_coordinator):
        """Return False when device connection_status is offline."""
        mock_outlet_device.state.connection_status = "offline"
        entity = VeSyncBaseEntity(mock_outlet_device, mock_coordinator)
        assert entity.available is False

    def test_device_info(self, mock_outlet_device, mock_coordinator):
        """Return correct device info dict."""
        entity = VeSyncBaseEntity(mock_outlet_device, mock_coordinator)
        info = entity.device_info
        assert info["name"] == "TestOutlet"
        assert info["model"] == "ESW15-USA"
        assert info["manufacturer"] == "VeSync"
        assert ("vesync", "outlet-cid") in info["identifiers"]


# ---------------------------------------------------------------------------
# VeSyncDevice tests
# ---------------------------------------------------------------------------


class TestVeSyncDevice:
    """Tests for VeSyncDevice."""

    def test_is_on_true(self, mock_outlet_device, mock_coordinator):
        """Return True when device_status is 'on'."""
        mock_outlet_device.state.device_status = "on"
        entity = VeSyncDevice(mock_outlet_device, mock_coordinator)
        assert entity.is_on is True

    def test_is_on_false(self, mock_outlet_device, mock_coordinator):
        """Return False when device_status is not 'on'."""
        mock_outlet_device.state.device_status = "off"
        entity = VeSyncDevice(mock_outlet_device, mock_coordinator)
        assert entity.is_on is False

    async def test_turn_off_calls_device(self, mock_outlet_device, mock_coordinator):
        """Delegate turn_off to the underlying device."""
        entity = VeSyncDevice(mock_outlet_device, mock_coordinator)
        await entity.async_turn_off()
        mock_outlet_device.turn_off.assert_called_once()
