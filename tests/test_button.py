"""Tests for VeSync button platform."""

from unittest.mock import MagicMock

import pytest

from custom_components.vesync.button import SENSOR_TYPES_CS158, VeSyncairfryerButton


class TestVeSyncAirfryerButton:
    """Tests for VeSyncairfryerButton entity."""

    @pytest.fixture
    def button_entity(self, mock_airfryer_device, mock_coordinator):
        """Return an airfryer button entity."""
        stype = SENSOR_TYPES_CS158["end"]
        return VeSyncairfryerButton(mock_airfryer_device, mock_coordinator, stype)

    def test_unique_id_suffix(self, button_entity):
        """Include button type in unique_id."""
        assert "end" in button_entity.unique_id

    def test_name(self, button_entity):
        """Return the button type name."""
        assert "End cooking" in button_entity.name

    def test_icon(self, button_entity):
        """Return the stop icon."""
        assert button_entity.icon == "mdi:stop"

    def test_press_calls_end(self, button_entity, mock_airfryer_device):
        """Delegate press to device.end."""
        button_entity.press()
        mock_airfryer_device.end.assert_called_once()
