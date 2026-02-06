"""Tests for VeSync number platform."""

from unittest.mock import MagicMock

import pytest

from homeassistant.helpers.entity import EntityCategory

from custom_components.vesync.number import (
    VeSyncFanSpeedLevelHA,
    VeSyncHumidifierMistLevelHA,
    VeSyncHumidifierTargetLevelHA,
    VeSyncHumidifierWarmthLevelHA,
)


# ---------------------------------------------------------------------------
# VeSyncFanSpeedLevelHA tests
# ---------------------------------------------------------------------------


class TestVeSyncFanSpeedLevelHA:
    """Tests for VeSyncFanSpeedLevelHA entity."""

    @pytest.fixture
    def speed_entity(self, mock_fan_device, mock_coordinator):
        """Return a fan speed level entity."""
        return VeSyncFanSpeedLevelHA(mock_fan_device, mock_coordinator)

    def test_unique_id_suffix(self, speed_entity):
        """Append -fan-speed-level to unique_id."""
        assert speed_entity.unique_id.endswith("-fan-speed-level")

    def test_name_suffix(self, speed_entity):
        """Append 'fan speed level' to name."""
        assert "fan speed level" in speed_entity.name

    def test_min_value(self, speed_entity):
        """Return minimum value from config levels."""
        assert speed_entity.native_min_value == 1

    def test_max_value(self, speed_entity):
        """Return maximum value from config levels."""
        assert speed_entity.native_max_value == 3

    def test_native_value(self, speed_entity, mock_fan_device):
        """Return current speed from device."""
        mock_fan_device.speed = 2
        assert speed_entity.native_value == 2

    def test_set_native_value(self, speed_entity, mock_fan_device):
        """Call change_fan_speed with integer value."""
        speed_entity.set_native_value(3)
        mock_fan_device.change_fan_speed.assert_called_once_with(3)

    def test_entity_category(self, speed_entity):
        """Return CONFIG entity category."""
        assert speed_entity.entity_category == EntityCategory.CONFIG

    def test_extra_state_attributes(self, speed_entity, mock_fan_device):
        """Return fan speed levels in attributes."""
        attrs = speed_entity.extra_state_attributes
        assert "fan speed levels" in attrs
        assert attrs["fan speed levels"] == [1, 2, 3]


# ---------------------------------------------------------------------------
# VeSyncHumidifierMistLevelHA tests
# ---------------------------------------------------------------------------


class TestVeSyncHumidifierMistLevelHA:
    """Tests for VeSyncHumidifierMistLevelHA entity."""

    @pytest.fixture
    def mist_entity(self, mock_humidifier_device, mock_coordinator):
        """Return a mist level entity."""
        return VeSyncHumidifierMistLevelHA(mock_humidifier_device, mock_coordinator)

    def test_unique_id_suffix(self, mist_entity):
        """Append -mist-level to unique_id."""
        assert mist_entity.unique_id.endswith("-mist-level")

    def test_min_max_values(self, mist_entity):
        """Set min/max from device mist_levels config."""
        assert mist_entity.native_min_value == 1
        assert mist_entity.native_max_value == 9

    def test_native_value(self, mist_entity, mock_humidifier_device):
        """Return mist_virtual_level from details."""
        assert mist_entity.native_value == 3

    def test_set_native_value(self, mist_entity, mock_humidifier_device):
        """Call set_mist_level with integer value."""
        mist_entity.set_native_value(5)
        mock_humidifier_device.set_mist_level.assert_called_once_with(5)


# ---------------------------------------------------------------------------
# VeSyncHumidifierWarmthLevelHA tests
# ---------------------------------------------------------------------------


class TestVeSyncHumidifierWarmthLevelHA:
    """Tests for VeSyncHumidifierWarmthLevelHA entity."""

    @pytest.fixture
    def warmth_entity(self, mock_humidifier_device, mock_coordinator):
        """Return a warm mist level entity."""
        return VeSyncHumidifierWarmthLevelHA(mock_humidifier_device, mock_coordinator)

    def test_unique_id_suffix(self, warmth_entity):
        """Append -warm-mist to unique_id."""
        assert warmth_entity.unique_id.endswith("-warm-mist")

    def test_min_max_values(self, warmth_entity):
        """Set min/max from device warm_mist_levels config."""
        assert warmth_entity.native_min_value == 0
        assert warmth_entity.native_max_value == 3

    def test_native_value(self, warmth_entity, mock_humidifier_device):
        """Return warm_mist_level from details."""
        assert warmth_entity.native_value == 0

    def test_set_native_value(self, warmth_entity, mock_humidifier_device):
        """Call set_warm_level with integer value."""
        warmth_entity.set_native_value(2)
        mock_humidifier_device.set_warm_level.assert_called_once_with(2)


# ---------------------------------------------------------------------------
# VeSyncHumidifierTargetLevelHA tests
# ---------------------------------------------------------------------------


class TestVeSyncHumidifierTargetLevelHA:
    """Tests for VeSyncHumidifierTargetLevelHA entity."""

    @pytest.fixture
    def target_entity(self, mock_humidifier_device, mock_coordinator):
        """Return a target humidity level entity."""
        return VeSyncHumidifierTargetLevelHA(mock_humidifier_device, mock_coordinator)

    def test_unique_id_suffix(self, target_entity):
        """Append -target-level to unique_id."""
        assert target_entity.unique_id.endswith("-target-level")

    def test_min_max_values(self, target_entity):
        """Set min/max from constants."""
        assert target_entity.native_min_value == 30
        assert target_entity.native_max_value == 80

    def test_native_value(self, target_entity, mock_humidifier_device):
        """Return auto_target_humidity from config."""
        assert target_entity.native_value == 55

    def test_set_native_value(self, target_entity, mock_humidifier_device):
        """Call set_humidity with integer value."""
        target_entity.set_native_value(60)
        mock_humidifier_device.set_humidity.assert_called_once_with(60)

    def test_unit(self, target_entity):
        """Return percentage unit."""
        from homeassistant.const import PERCENTAGE

        assert target_entity.native_unit_of_measurement == PERCENTAGE
