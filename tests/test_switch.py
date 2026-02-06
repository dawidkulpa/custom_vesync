"""Tests for VeSync switch platform."""

from unittest.mock import MagicMock

import pytest

from custom_components.vesync.switch import (
    VeSyncBaseSwitch,
    VeSyncFanChildLockHA,
    VeSyncHumidifierAutomaticStopHA,
    VeSyncHumidifierAutoOnHA,
    VeSyncHumidifierDisplayHA,
    VeSyncLightSwitch,
    VeSyncSwitchHA,
)


# ---------------------------------------------------------------------------
# VeSyncBaseSwitch / VeSyncSwitchHA tests
# ---------------------------------------------------------------------------


class TestVeSyncSwitchHA:
    """Tests for VeSyncSwitchHA (outlet) entity."""

    @pytest.fixture
    def switch_entity(self, mock_outlet_device, mock_coordinator):
        """Return a VeSyncSwitchHA entity."""
        return VeSyncSwitchHA(mock_outlet_device, mock_coordinator)

    def test_turn_on(self, switch_entity, mock_outlet_device):
        """Delegate turn_on to the device."""
        switch_entity.turn_on()
        mock_outlet_device.turn_on.assert_called_once()

    def test_turn_off(self, switch_entity, mock_outlet_device):
        """Delegate turn_off to the device."""
        switch_entity.turn_off()
        mock_outlet_device.turn_off.assert_called_once()

    def test_extra_state_attributes_with_energy(self, switch_entity, mock_outlet_device):
        """Return energy attributes when available."""
        attrs = switch_entity.extra_state_attributes
        assert "voltage" in attrs
        assert "weekly_energy_total" in attrs
        assert "monthly_energy_total" in attrs
        assert "yearly_energy_total" in attrs

    def test_extra_state_attributes_without_energy(self, mock_coordinator):
        """Return empty dict when energy info unavailable."""
        device = MagicMock(spec=["device_name", "device_type", "cid", "uuid",
                                  "connection_status", "device_status",
                                  "sub_device_no", "current_firm_version",
                                  "turn_on", "turn_off"])
        device.device_name = "NoEnergyOutlet"
        device.device_type = "ESW15-USA"
        device.cid = "test-cid"
        device.sub_device_no = None
        device.connection_status = "online"
        device.device_status = "on"
        device.current_firm_version = "1.0"

        switch = VeSyncSwitchHA(device, mock_coordinator)
        assert switch.extra_state_attributes == {}

    def test_update_calls_device_methods(self, switch_entity, mock_outlet_device):
        """Delegate update to device.update and device.update_energy."""
        switch_entity.update()
        mock_outlet_device.update.assert_called_once()
        mock_outlet_device.update_energy.assert_called_once()


class TestVeSyncLightSwitch:
    """Tests for VeSyncLightSwitch entity."""

    def test_turn_on(self, mock_wall_switch_device, mock_coordinator):
        """Delegate turn_on to the device."""
        switch = VeSyncLightSwitch(mock_wall_switch_device, mock_coordinator)
        switch.turn_on()
        mock_wall_switch_device.turn_on.assert_called_once()


# ---------------------------------------------------------------------------
# Feature toggle switch tests
# ---------------------------------------------------------------------------


class TestVeSyncFanChildLockHA:
    """Tests for child lock switch entity."""

    @pytest.fixture
    def child_lock_entity(self, mock_humidifier_device, mock_coordinator):
        """Return a child lock entity."""
        mock_humidifier_device.details = {"child_lock": True}
        return VeSyncFanChildLockHA(mock_humidifier_device, mock_coordinator)

    def test_unique_id_suffix(self, child_lock_entity):
        """Append -child-lock to unique_id."""
        assert child_lock_entity.unique_id.endswith("-child-lock")

    def test_name_suffix(self, child_lock_entity):
        """Append 'child lock' to entity name."""
        assert child_lock_entity.name.endswith("child lock")

    def test_is_on(self, child_lock_entity, mock_humidifier_device):
        """Return child_lock state from device details."""
        mock_humidifier_device.details = {"child_lock": True}
        assert child_lock_entity.is_on is True

    def test_turn_on(self, child_lock_entity, mock_humidifier_device):
        """Delegate to device.child_lock_on."""
        child_lock_entity.turn_on()
        mock_humidifier_device.child_lock_on.assert_called_once()

    def test_turn_off(self, child_lock_entity, mock_humidifier_device):
        """Delegate to device.child_lock_off."""
        child_lock_entity.turn_off()
        mock_humidifier_device.child_lock_off.assert_called_once()


class TestVeSyncHumidifierDisplayHA:
    """Tests for display toggle switch entity."""

    @pytest.fixture
    def display_entity(self, mock_humidifier_device, mock_coordinator):
        """Return a display switch entity."""
        mock_humidifier_device.details = {"display": True}
        return VeSyncHumidifierDisplayHA(mock_humidifier_device, mock_coordinator)

    def test_unique_id_suffix(self, display_entity):
        """Append -display to unique_id."""
        assert display_entity.unique_id.endswith("-display")

    def test_is_on(self, display_entity, mock_humidifier_device):
        """Return display state from device details."""
        mock_humidifier_device.details = {"display": True}
        assert display_entity.is_on is True

    def test_turn_on(self, display_entity, mock_humidifier_device):
        """Delegate to device.turn_on_display."""
        display_entity.turn_on()
        mock_humidifier_device.turn_on_display.assert_called_once()

    def test_turn_off(self, display_entity, mock_humidifier_device):
        """Delegate to device.turn_off_display."""
        display_entity.turn_off()
        mock_humidifier_device.turn_off_display.assert_called_once()


class TestVeSyncHumidifierAutomaticStopHA:
    """Tests for automatic stop switch entity."""

    @pytest.fixture
    def auto_stop_entity(self, mock_humidifier_device, mock_coordinator):
        """Return an automatic stop entity."""
        return VeSyncHumidifierAutomaticStopHA(mock_humidifier_device, mock_coordinator)

    def test_unique_id_suffix(self, auto_stop_entity):
        """Append -automatic-stop to unique_id."""
        assert auto_stop_entity.unique_id.endswith("-automatic-stop")

    def test_is_on(self, auto_stop_entity, mock_humidifier_device):
        """Return automatic_stop state from device config."""
        assert auto_stop_entity.is_on is True

    def test_turn_on(self, auto_stop_entity, mock_humidifier_device):
        """Delegate to device.automatic_stop_on."""
        auto_stop_entity.turn_on()
        mock_humidifier_device.automatic_stop_on.assert_called_once()

    def test_turn_off(self, auto_stop_entity, mock_humidifier_device):
        """Delegate to device.automatic_stop_off."""
        auto_stop_entity.turn_off()
        mock_humidifier_device.automatic_stop_off.assert_called_once()


class TestVeSyncHumidifierAutoOnHA:
    """Tests for auto mode switch entity."""

    @pytest.fixture
    def auto_mode_entity(self, mock_humidifier_device, mock_coordinator):
        """Return an auto mode entity."""
        return VeSyncHumidifierAutoOnHA(mock_humidifier_device, mock_coordinator)

    def test_unique_id_suffix(self, auto_mode_entity):
        """Append -auto-mode to unique_id."""
        assert auto_mode_entity.unique_id.endswith("-auto-mode")

    def test_is_on_in_auto(self, auto_mode_entity, mock_humidifier_device):
        """Return True when mode is 'auto'."""
        mock_humidifier_device.details = {"mode": "auto"}
        assert auto_mode_entity.is_on is True

    def test_is_on_not_auto(self, auto_mode_entity, mock_humidifier_device):
        """Return False when mode is not 'auto'."""
        mock_humidifier_device.details = {"mode": "manual"}
        assert auto_mode_entity.is_on is False

    def test_turn_on(self, auto_mode_entity, mock_humidifier_device):
        """Delegate to device.set_auto_mode."""
        auto_mode_entity.turn_on()
        mock_humidifier_device.set_auto_mode.assert_called_once()

    def test_turn_off(self, auto_mode_entity, mock_humidifier_device):
        """Set manual mode and mist level 1."""
        auto_mode_entity.turn_off()
        mock_humidifier_device.set_manual_mode.assert_called_once()
        mock_humidifier_device.set_mist_level.assert_called_once_with(1)
