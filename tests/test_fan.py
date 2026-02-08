"""Tests for VeSync fan platform."""

import math
from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.components.fan import FanEntityFeature
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from custom_components.vesync.const import (
    VS_MODE_AUTO,
    VS_MODE_MANUAL,
    VS_MODE_SLEEP,
    VS_MODE_TURBO,
)
from custom_components.vesync.fan import VeSyncFanHA


class TestVeSyncFanHA:
    """Tests for VeSyncFanHA entity."""

    @pytest.fixture
    def fan_entity(self, mock_fan_device, mock_coordinator):
        """Return a VeSyncFanHA entity."""
        return VeSyncFanHA(mock_fan_device, mock_coordinator)

    def test_speed_range_from_config(self, fan_entity):
        """Set speed range from device config levels."""
        assert fan_entity._speed_range == (1, 3)

    def test_speed_count(self, fan_entity):
        """Return correct speed count based on range."""
        assert fan_entity.speed_count == 3

    def test_preset_modes_from_config(self, fan_entity):
        """Set preset modes from device config."""
        assert VS_MODE_MANUAL in fan_entity.preset_modes
        assert VS_MODE_AUTO in fan_entity.preset_modes
        assert VS_MODE_SLEEP in fan_entity.preset_modes

    def test_supported_features_with_multiple_speeds(self, fan_entity):
        """Support SET_SPEED and PRESET_MODE when speed_count > 1."""
        assert fan_entity.supported_features == (
            FanEntityFeature.SET_SPEED | FanEntityFeature.PRESET_MODE
        )

    def test_supported_features_single_speed(self, mock_coordinator):
        """Support only SET_SPEED when speed_count is 1."""
        device = MagicMock()
        device.device_type = "TestFan"
        device.fan_levels = [1]
        device.modes = []
        device.cid = "test"
        device.sub_device_no = None
        device.device_name = "Test"
        device.connection_status = "online"
        device.current_firm_version = "1.0"

        fan = VeSyncFanHA(device, mock_coordinator)
        assert fan.supported_features == FanEntityFeature.SET_SPEED

    def test_percentage_in_manual_mode(self, fan_entity, mock_fan_device):
        """Return percentage when in manual mode."""
        mock_fan_device.state.mode = VS_MODE_MANUAL
        mock_fan_device.state.fan_level = 2
        expected = ranged_value_to_percentage((1, 3), 2)
        assert fan_entity.percentage == expected

    def test_percentage_none_in_auto_mode(self, fan_entity, mock_fan_device):
        """Return None when not in manual mode."""
        mock_fan_device.state.mode = VS_MODE_AUTO
        assert fan_entity.percentage is None

    def test_preset_mode_returns_device_mode(self, fan_entity, mock_fan_device):
        """Return the current device mode."""
        mock_fan_device.state.mode = VS_MODE_SLEEP
        assert fan_entity.preset_mode == VS_MODE_SLEEP

    async def test_set_percentage_turns_off_at_zero(self, fan_entity, mock_fan_device):
        """Turn off the fan when percentage is 0."""
        await fan_entity.async_set_percentage(0)
        mock_fan_device.turn_off.assert_called_once()

    async def test_set_percentage_turns_on_if_off(self, fan_entity, mock_fan_device):
        """Turn on the fan if it is off when setting percentage."""
        mock_fan_device.is_on = False
        await fan_entity.async_set_percentage(50)
        mock_fan_device.turn_on.assert_called_once()
        mock_fan_device.set_manual_mode.assert_called_once()

    async def test_set_percentage_sets_speed(self, fan_entity, mock_fan_device):
        """Set the fan speed to the correct level."""
        mock_fan_device.is_on = True
        await fan_entity.async_set_percentage(100)
        expected_level = math.ceil(
            percentage_to_ranged_value((1, 3), 100)
        )
        mock_fan_device.set_fan_speed.assert_called_with(expected_level)

    async def test_set_preset_mode_auto(self, fan_entity, mock_fan_device):
        """Set auto mode on the device."""
        mock_fan_device.is_on = True
        await fan_entity.async_set_preset_mode(VS_MODE_AUTO)
        mock_fan_device.set_auto_mode.assert_called_once()

    async def test_set_preset_mode_sleep(self, fan_entity, mock_fan_device):
        """Set sleep mode on the device."""
        mock_fan_device.is_on = True
        await fan_entity.async_set_preset_mode(VS_MODE_SLEEP)
        mock_fan_device.set_sleep_mode.assert_called_once()

    async def test_set_preset_mode_manual(self, fan_entity, mock_fan_device):
        """Set manual mode on the device."""
        mock_fan_device.is_on = True
        await fan_entity.async_set_preset_mode(VS_MODE_MANUAL)
        mock_fan_device.set_manual_mode.assert_called_once()

    async def test_set_invalid_preset_mode_raises(self, fan_entity):
        """Raise ValueError for invalid preset mode."""
        with pytest.raises(ValueError):
            await fan_entity.async_set_preset_mode("invalid_mode")

    async def test_turn_on_with_preset_mode(self, fan_entity, mock_fan_device):
        """Turn on with preset mode delegates to set_preset_mode."""
        mock_fan_device.is_on = True
        await fan_entity.async_turn_on(preset_mode=VS_MODE_AUTO)
        mock_fan_device.set_auto_mode.assert_called_once()

    async def test_turn_on_with_percentage(self, fan_entity, mock_fan_device):
        """Turn on with specific percentage."""
        mock_fan_device.is_on = True
        await fan_entity.async_turn_on(percentage=75)
        mock_fan_device.set_manual_mode.assert_called()

    async def test_turn_on_default_percentage(self, fan_entity, mock_fan_device):
        """Turn on with default 50% when no arguments given."""
        mock_fan_device.is_on = True
        await fan_entity.async_turn_on()
        mock_fan_device.set_manual_mode.assert_called()

    def test_extra_state_attributes(self, fan_entity, mock_fan_device):
        """Return extra state attributes from device details."""
        mock_fan_device.state.to_dict = MagicMock(return_value={"humidity": 45, "some_other": "value"})
        attrs = fan_entity.extra_state_attributes
        # humidity gets remapped to current_humidity
        assert "current_humidity" in attrs

    def test_lv_pur131s_speed_range(self, mock_coordinator):
        """Set speed range to (1, 3) for LV-PUR131S."""
        device = MagicMock()
        device.device_type = "LV-PUR131S"
        device.fan_levels = []
        device.modes = []
        device.cid = "test"
        device.sub_device_no = None
        device.device_name = "Purifier"
        device.connection_status = "online"
        device.current_firm_version = "1.0"

        fan = VeSyncFanHA(device, mock_coordinator)
        assert fan._speed_range == (1, 3)
