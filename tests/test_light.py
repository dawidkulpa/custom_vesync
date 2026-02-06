"""Tests for VeSync light platform."""

from unittest.mock import MagicMock

import pytest

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    COLOR_MODE_BRIGHTNESS,
    COLOR_MODE_COLOR_TEMP,
)

from custom_components.vesync.light import (
    VeSyncDimmableLightHA,
    VeSyncNightLightHA,
    VeSyncTunableWhiteLightHA,
    _ha_brightness_to_vesync,
    _vesync_brightness_to_ha,
)


# ---------------------------------------------------------------------------
# Brightness conversion tests
# ---------------------------------------------------------------------------


class TestBrightnessConversion:
    """Tests for brightness conversion helpers."""

    def test_vesync_to_ha_mid_range(self):
        """Convert 50% VeSync brightness to HA range."""
        result = _vesync_brightness_to_ha(50)
        assert result == round((50 / 100) * 255)

    def test_vesync_to_ha_full(self):
        """Convert 100% VeSync brightness to 255."""
        assert _vesync_brightness_to_ha(100) == 255

    def test_vesync_to_ha_minimum(self):
        """Convert 1% VeSync brightness to minimum HA value."""
        result = _vesync_brightness_to_ha(1)
        assert result == round((1 / 100) * 255)

    def test_vesync_to_ha_zero_clamps_to_one(self):
        """Clamp zero brightness to at least 1 before converting."""
        result = _vesync_brightness_to_ha(0)
        assert result == round((1 / 100) * 255)

    def test_vesync_to_ha_invalid_returns_none(self):
        """Return None for non-numeric brightness values."""
        assert _vesync_brightness_to_ha("invalid") is None

    def test_ha_to_vesync_full(self):
        """Convert 255 HA brightness to 100%."""
        assert _ha_brightness_to_vesync(255) == 100

    def test_ha_to_vesync_minimum(self):
        """Convert 1 HA brightness to at least 1%."""
        assert _ha_brightness_to_vesync(1) >= 1

    def test_ha_to_vesync_mid_range(self):
        """Convert mid-range HA brightness to percent."""
        result = _ha_brightness_to_vesync(128)
        assert 1 <= result <= 100

    def test_ha_to_vesync_clamps_max(self):
        """Clamp values above 255 to 100%."""
        assert _ha_brightness_to_vesync(300) == 100

    def test_roundtrip_conversion(self):
        """Round-trip conversion preserves approximate value."""
        for vesync_val in [10, 25, 50, 75, 100]:
            ha_val = _vesync_brightness_to_ha(vesync_val)
            back = _ha_brightness_to_vesync(ha_val)
            assert abs(back - vesync_val) <= 1


# ---------------------------------------------------------------------------
# VeSyncDimmableLightHA tests
# ---------------------------------------------------------------------------


class TestVeSyncDimmableLightHA:
    """Tests for VeSyncDimmableLightHA entity."""

    @pytest.fixture
    def light_entity(self, mock_bulb_dimmable_device, mock_coordinator):
        """Return a dimmable light entity."""
        return VeSyncDimmableLightHA(mock_bulb_dimmable_device, mock_coordinator)

    def test_color_mode(self, light_entity):
        """Return BRIGHTNESS color mode."""
        assert light_entity.color_mode == COLOR_MODE_BRIGHTNESS

    def test_supported_color_modes(self, light_entity):
        """Return list with BRIGHTNESS color mode."""
        assert light_entity.supported_color_modes == [COLOR_MODE_BRIGHTNESS]

    def test_brightness(self, light_entity, mock_bulb_dimmable_device):
        """Return converted brightness value."""
        mock_bulb_dimmable_device.brightness = 75
        expected = _vesync_brightness_to_ha(75)
        assert light_entity.brightness == expected

    def test_turn_on_no_args(self, light_entity, mock_bulb_dimmable_device):
        """Turn on the light without arguments."""
        light_entity.turn_on()
        mock_bulb_dimmable_device.turn_on.assert_called_once()

    def test_turn_on_with_brightness(self, light_entity, mock_bulb_dimmable_device):
        """Set brightness when turning on."""
        light_entity.turn_on(**{ATTR_BRIGHTNESS: 200})
        mock_bulb_dimmable_device.set_brightness.assert_called_once()
        # Should NOT call turn_on (attribute_adjustment_only)
        mock_bulb_dimmable_device.turn_on.assert_not_called()


# ---------------------------------------------------------------------------
# VeSyncTunableWhiteLightHA tests
# ---------------------------------------------------------------------------


class TestVeSyncTunableWhiteLightHA:
    """Tests for VeSyncTunableWhiteLightHA entity."""

    @pytest.fixture
    def light_entity(self, mock_bulb_tunable_device, mock_coordinator):
        """Return a tunable white light entity."""
        return VeSyncTunableWhiteLightHA(mock_bulb_tunable_device, mock_coordinator)

    def test_color_mode(self, light_entity):
        """Return COLOR_TEMP color mode."""
        assert light_entity.color_mode == COLOR_MODE_COLOR_TEMP

    def test_supported_color_modes(self, light_entity):
        """Return list with COLOR_TEMP color mode."""
        assert light_entity.supported_color_modes == [COLOR_MODE_COLOR_TEMP]

    def test_min_mireds(self, light_entity):
        """Return 154 for minimum mireds (6500K)."""
        assert light_entity.min_mireds == 154

    def test_max_mireds(self, light_entity):
        """Return 370 for maximum mireds (2700K)."""
        assert light_entity.max_mireds == 370

    def test_color_temp_conversion(self, light_entity, mock_bulb_tunable_device):
        """Convert VeSync color temp percentage to mireds."""
        mock_bulb_tunable_device.color_temp_pct = 50
        result = light_entity.color_temp
        assert 154 <= result <= 370

    def test_color_temp_invalid_returns_zero(self, light_entity, mock_bulb_tunable_device):
        """Return 0 for non-numeric color temp values."""
        mock_bulb_tunable_device.color_temp_pct = "invalid"
        assert light_entity.color_temp == 0

    def test_turn_on_with_color_temp(self, light_entity, mock_bulb_tunable_device):
        """Set color temp when turning on."""
        light_entity.turn_on(**{ATTR_COLOR_TEMP: 250})
        mock_bulb_tunable_device.set_color_temp.assert_called_once()
        # Should NOT call turn_on (attribute_adjustment_only)
        mock_bulb_tunable_device.turn_on.assert_not_called()

    def test_turn_on_with_both(self, light_entity, mock_bulb_tunable_device):
        """Set both color temp and brightness."""
        light_entity.turn_on(**{ATTR_COLOR_TEMP: 250, ATTR_BRIGHTNESS: 200})
        mock_bulb_tunable_device.set_color_temp.assert_called_once()
        mock_bulb_tunable_device.set_brightness.assert_called_once()
        mock_bulb_tunable_device.turn_on.assert_not_called()


# ---------------------------------------------------------------------------
# VeSyncNightLightHA tests
# ---------------------------------------------------------------------------


class TestVeSyncNightLightHA:
    """Tests for VeSyncNightLightHA entity."""

    @pytest.fixture
    def night_light_device(self, mock_fan_device):
        """Return a mock device with night light."""
        mock_fan_device.night_light = True
        mock_fan_device.details = {
            "night_light": "on",
            "night_light_brightness": 50,
        }
        return mock_fan_device

    @pytest.fixture
    def night_light_entity(self, night_light_device, mock_coordinator):
        """Return a VeSyncNightLightHA entity."""
        return VeSyncNightLightHA(night_light_device, mock_coordinator)

    def test_unique_id_suffix(self, night_light_entity):
        """Append -night-light to unique_id."""
        assert night_light_entity.unique_id.endswith("-night-light")

    def test_name_suffix(self, night_light_entity):
        """Append 'night light' to entity name."""
        assert night_light_entity.name.endswith("night light")

    def test_is_on_with_night_light_on(self, night_light_entity, night_light_device):
        """Return True when night_light is 'on'."""
        night_light_device.details["night_light"] = "on"
        assert night_light_entity.is_on is True

    def test_is_on_with_night_light_dim(self, night_light_entity, night_light_device):
        """Return True when night_light is 'dim'."""
        night_light_device.details["night_light"] = "dim"
        assert night_light_entity.is_on is True

    def test_is_on_with_night_light_off(self, night_light_entity, night_light_device):
        """Return False when night_light is 'off'."""
        night_light_device.details["night_light"] = "off"
        assert night_light_entity.is_on is False

    def test_brightness_with_numeric(self, night_light_entity, night_light_device):
        """Return converted brightness for numeric night_light_brightness."""
        night_light_device.details["night_light_brightness"] = 50
        expected = _vesync_brightness_to_ha(50)
        assert night_light_entity.brightness == expected

    def test_turn_on_fan_type_full(self, night_light_entity, night_light_device):
        """Call set_night_light('on') for fan types at full brightness."""
        night_light_device._config_dict = {"module": "VeSyncAirBypass"}
        night_light_entity.turn_on(**{ATTR_BRIGHTNESS: 255})
        night_light_device.set_night_light.assert_called_with("on")

    def test_turn_on_fan_type_dim(self, night_light_entity, night_light_device):
        """Call set_night_light('dim') for fan types at lower brightness."""
        night_light_device._config_dict = {"module": "VeSyncAirBypass"}
        night_light_entity.turn_on(**{ATTR_BRIGHTNESS: 100})
        night_light_device.set_night_light.assert_called_with("dim")

    def test_turn_off_fan_type(self, night_light_entity, night_light_device):
        """Call set_night_light('off') for fan types."""
        night_light_device._config_dict = {"module": "VeSyncAirBypass"}
        night_light_entity.turn_off()
        night_light_device.set_night_light.assert_called_with("off")

    def test_turn_on_non_fan_with_brightness(self, mock_coordinator):
        """Call set_night_light_brightness for non-fan types."""
        device = MagicMock()
        device.device_type = "LUH-D301S-WEU"
        device.cid = "test"
        device.sub_device_no = None
        device.device_name = "Humidifier"
        device.connection_status = "online"
        device.current_firm_version = "1.0"
        device.night_light = True
        device.details = {
            "night_light_brightness": 50,
        }
        device._config_dict = {"module": "VeSyncHumid200300S"}

        entity = VeSyncNightLightHA(device, mock_coordinator)
        entity.turn_on(**{ATTR_BRIGHTNESS: 200})
        device.set_night_light_brightness.assert_called_once()

    def test_turn_off_non_fan(self, mock_coordinator):
        """Call set_night_light_brightness(0) for non-fan types."""
        device = MagicMock()
        device.device_type = "LUH-D301S-WEU"
        device.cid = "test"
        device.sub_device_no = None
        device.device_name = "Humidifier"
        device.connection_status = "online"
        device.current_firm_version = "1.0"
        device.night_light = True
        device.details = {
            "night_light_brightness": 50,
        }
        device._config_dict = {"module": "VeSyncHumid200300S"}

        entity = VeSyncNightLightHA(device, mock_coordinator)
        entity.turn_off()
        device.set_night_light_brightness.assert_called_with(0)
