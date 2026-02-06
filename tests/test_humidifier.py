"""Tests for VeSync humidifier platform."""

from unittest.mock import MagicMock

import pytest

from homeassistant.components.humidifier.const import (
    MODE_AUTO,
    MODE_NORMAL,
    MODE_SLEEP,
    HumidifierEntityFeature,
)

from custom_components.vesync.humidifier import (
    MAX_HUMIDITY,
    MIN_HUMIDITY,
    VeSyncHumidifierHA,
    _get_ha_mode,
    _get_vs_mode,
)


# ---------------------------------------------------------------------------
# Mode mapping tests
# ---------------------------------------------------------------------------


class TestModeMapping:
    """Tests for mode mapping helpers."""

    def test_get_ha_mode_auto(self):
        """Map VeSync 'auto' to HA MODE_AUTO."""
        assert _get_ha_mode("auto") == MODE_AUTO

    def test_get_ha_mode_humidity(self):
        """Map VeSync 'humidity' to HA MODE_AUTO."""
        assert _get_ha_mode("humidity") == MODE_AUTO

    def test_get_ha_mode_manual(self):
        """Map VeSync 'manual' to HA MODE_NORMAL."""
        assert _get_ha_mode("manual") == MODE_NORMAL

    def test_get_ha_mode_sleep(self):
        """Map VeSync 'sleep' to HA MODE_SLEEP."""
        assert _get_ha_mode("sleep") == MODE_SLEEP

    def test_get_ha_mode_unknown_returns_none(self):
        """Return None for unknown VeSync mode."""
        assert _get_ha_mode("turbo") is None

    def test_get_vs_mode_auto(self):
        """Map HA MODE_AUTO to VeSync mode."""
        result = _get_vs_mode(MODE_AUTO)
        assert result is not None

    def test_get_vs_mode_normal(self):
        """Map HA MODE_NORMAL to VeSync 'manual'."""
        assert _get_vs_mode(MODE_NORMAL) == "manual"

    def test_get_vs_mode_sleep(self):
        """Map HA MODE_SLEEP to VeSync 'sleep'."""
        assert _get_vs_mode(MODE_SLEEP) == "sleep"

    def test_get_vs_mode_unknown_returns_none(self):
        """Return None for unknown HA mode."""
        assert _get_vs_mode("invalid") is None


# ---------------------------------------------------------------------------
# VeSyncHumidifierHA tests
# ---------------------------------------------------------------------------


class TestVeSyncHumidifierHA:
    """Tests for VeSyncHumidifierHA entity."""

    @pytest.fixture
    def humidifier_entity(self, mock_humidifier_device, mock_coordinator):
        """Return a VeSyncHumidifierHA entity."""
        return VeSyncHumidifierHA(mock_humidifier_device, mock_coordinator)

    def test_min_humidity(self, humidifier_entity):
        """Return correct minimum humidity."""
        assert humidifier_entity.min_humidity == MIN_HUMIDITY

    def test_max_humidity(self, humidifier_entity):
        """Return correct maximum humidity."""
        assert humidifier_entity.max_humidity == MAX_HUMIDITY

    def test_supported_features(self, humidifier_entity):
        """Support MODES feature."""
        assert humidifier_entity.supported_features == HumidifierEntityFeature.MODES

    def test_target_humidity(self, humidifier_entity, mock_humidifier_device):
        """Return target humidity from device config."""
        assert humidifier_entity.target_humidity == 55

    def test_mode(self, humidifier_entity, mock_humidifier_device):
        """Return current mode mapped to HA."""
        mock_humidifier_device.details = {"mode": "auto"}
        assert humidifier_entity.mode == MODE_AUTO

    def test_is_on(self, humidifier_entity, mock_humidifier_device):
        """Return enabled state from device."""
        mock_humidifier_device.enabled = True
        assert humidifier_entity.is_on is True

    def test_is_off(self, humidifier_entity, mock_humidifier_device):
        """Return False when device is disabled."""
        mock_humidifier_device.enabled = False
        assert humidifier_entity.is_on is False

    def test_available_modes(self, humidifier_entity, mock_humidifier_device):
        """Return available modes mapped to HA."""
        modes = humidifier_entity.available_modes
        assert MODE_AUTO in modes
        assert MODE_NORMAL in modes
        assert MODE_SLEEP in modes

    def test_set_humidity_valid(self, humidifier_entity, mock_humidifier_device):
        """Set humidity within valid range."""
        humidifier_entity.set_humidity(50)
        mock_humidifier_device.set_humidity.assert_called_once_with(50)

    def test_set_humidity_out_of_range(self, humidifier_entity):
        """Raise ValueError for humidity outside valid range."""
        with pytest.raises(ValueError):
            humidifier_entity.set_humidity(10)

    def test_set_humidity_device_failure(self, humidifier_entity, mock_humidifier_device):
        """Raise ValueError when device returns failure."""
        mock_humidifier_device.set_humidity.return_value = False
        with pytest.raises(ValueError, match="error occurred"):
            humidifier_entity.set_humidity(50)

    def test_set_mode_auto(self, humidifier_entity, mock_humidifier_device):
        """Set mode to auto."""
        humidifier_entity.set_mode(MODE_AUTO)
        mock_humidifier_device.set_humidity_mode.assert_called_once()

    def test_set_mode_invalid(self, humidifier_entity):
        """Raise ValueError for invalid mode."""
        with pytest.raises(ValueError):
            humidifier_entity.set_mode("turbo")

    def test_set_mode_device_failure(self, humidifier_entity, mock_humidifier_device):
        """Raise ValueError when set_humidity_mode returns failure."""
        mock_humidifier_device.set_humidity_mode.return_value = False
        with pytest.raises(ValueError, match="error occurred"):
            humidifier_entity.set_mode(MODE_AUTO)

    def test_turn_on(self, humidifier_entity, mock_humidifier_device):
        """Turn on the humidifier."""
        mock_humidifier_device.turn_on.return_value = True
        humidifier_entity.turn_on()
        mock_humidifier_device.turn_on.assert_called_once()

    def test_turn_on_failure(self, humidifier_entity, mock_humidifier_device):
        """Raise ValueError when turn_on fails."""
        mock_humidifier_device.turn_on.return_value = False
        with pytest.raises(ValueError, match="error occurred"):
            humidifier_entity.turn_on()

    def test_turn_off(self, humidifier_entity, mock_humidifier_device):
        """Turn off the humidifier."""
        mock_humidifier_device.turn_off.return_value = True
        humidifier_entity.turn_off()
        mock_humidifier_device.turn_off.assert_called_once()

    def test_turn_off_failure(self, humidifier_entity, mock_humidifier_device):
        """Raise ValueError when turn_off fails."""
        mock_humidifier_device.turn_off.return_value = False
        with pytest.raises(ValueError, match="error occurred"):
            humidifier_entity.turn_off()

    def test_extra_state_attributes(self, humidifier_entity, mock_humidifier_device):
        """Return mapped extra state attributes."""
        mock_humidifier_device.details = {
            "humidity": 55,
            "mode": "auto",
            "mist_level": 3,
        }
        attrs = humidifier_entity.extra_state_attributes
        # humidity gets remapped to current_humidity
        assert "current_humidity" in attrs
