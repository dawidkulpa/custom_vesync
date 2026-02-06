"""Tests for VeSync integration setup and teardown."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.vesync import async_setup_entry, async_unload_entry
from custom_components.vesync.const import (
    DOMAIN,
    SERVICE_UPDATE_DEVS,
    VS_BINARY_SENSORS,
    VS_BUTTON,
    VS_FANS,
    VS_HUMIDIFIERS,
    VS_LIGHTS,
    VS_MANAGER,
    VS_NUMBERS,
    VS_SENSORS,
    VS_SWITCHES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config_entry(hass):
    """Create a real-ish MockConfigEntry."""
    from unittest.mock import MagicMock

    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.domain = DOMAIN
    entry.data = {
        CONF_USERNAME: "test@example.com",
        CONF_PASSWORD: "test_password",
    }
    entry.options = {}
    return entry


# ---------------------------------------------------------------------------
# async_setup_entry tests
# ---------------------------------------------------------------------------


class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    async def test_successful_setup(self, hass: HomeAssistant):
        """Set up integration successfully with a valid login."""
        entry = _make_config_entry(hass)

        with (
            patch("custom_components.vesync.VeSync") as mock_vesync_class,
            patch(
                "custom_components.vesync.async_process_devices"
            ) as mock_process,
        ):
            manager = mock_vesync_class.return_value
            manager.login = MagicMock(return_value=True)
            manager.update = MagicMock()

            mock_process.return_value = {
                VS_SWITCHES: [],
                VS_FANS: [],
                VS_LIGHTS: [],
                VS_SENSORS: [],
                VS_HUMIDIFIERS: [],
                VS_NUMBERS: [],
                VS_BINARY_SENSORS: [],
                VS_BUTTON: [],
            }

            result = await async_setup_entry(hass, entry)

        assert result is True
        assert DOMAIN in hass.data
        assert entry.entry_id in hass.data[DOMAIN]
        assert VS_MANAGER in hass.data[DOMAIN][entry.entry_id]

    async def test_failed_login_returns_false(self, hass: HomeAssistant):
        """Return False when VeSync login fails."""
        entry = _make_config_entry(hass)

        with patch("custom_components.vesync.VeSync") as mock_vesync_class:
            manager = mock_vesync_class.return_value
            manager.login = MagicMock(return_value=False)

            result = await async_setup_entry(hass, entry)

        assert result is False

    async def test_coordinator_is_created(self, hass: HomeAssistant):
        """Create a DataUpdateCoordinator on setup."""
        entry = _make_config_entry(hass)

        with (
            patch("custom_components.vesync.VeSync") as mock_vesync_class,
            patch(
                "custom_components.vesync.async_process_devices"
            ) as mock_process,
        ):
            manager = mock_vesync_class.return_value
            manager.login = MagicMock(return_value=True)
            manager.update = MagicMock()

            mock_process.return_value = {
                VS_SWITCHES: [],
                VS_FANS: [],
                VS_LIGHTS: [],
                VS_SENSORS: [],
                VS_HUMIDIFIERS: [],
                VS_NUMBERS: [],
                VS_BINARY_SENSORS: [],
                VS_BUTTON: [],
            }

            await async_setup_entry(hass, entry)

        assert "coordinator" in hass.data[DOMAIN][entry.entry_id]

    async def test_coordinator_update_failure_raises(self, hass: HomeAssistant):
        """Raise UpdateFailed when manager.update raises an exception."""
        entry = _make_config_entry(hass)

        with (
            patch("custom_components.vesync.VeSync") as mock_vesync_class,
            patch(
                "custom_components.vesync.async_process_devices"
            ) as mock_process,
        ):
            manager = mock_vesync_class.return_value
            manager.login = MagicMock(return_value=True)
            manager.update = MagicMock(side_effect=RuntimeError("Connection error"))

            mock_process.return_value = {
                VS_SWITCHES: [],
                VS_FANS: [],
                VS_LIGHTS: [],
                VS_SENSORS: [],
                VS_HUMIDIFIERS: [],
                VS_NUMBERS: [],
                VS_BINARY_SENSORS: [],
                VS_BUTTON: [],
            }

            # The setup should still succeed (coordinator catches the error)
            result = await async_setup_entry(hass, entry)

        assert result is True
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
        # The coordinator should have recorded the update failure
        assert coordinator.last_update_success is False

    async def test_service_registered(self, hass: HomeAssistant):
        """Register the update_devices service on setup."""
        entry = _make_config_entry(hass)

        with (
            patch("custom_components.vesync.VeSync") as mock_vesync_class,
            patch(
                "custom_components.vesync.async_process_devices"
            ) as mock_process,
        ):
            manager = mock_vesync_class.return_value
            manager.login = MagicMock(return_value=True)
            manager.update = MagicMock()

            mock_process.return_value = {
                VS_SWITCHES: [],
                VS_FANS: [],
                VS_LIGHTS: [],
                VS_SENSORS: [],
                VS_HUMIDIFIERS: [],
                VS_NUMBERS: [],
                VS_BINARY_SENSORS: [],
                VS_BUTTON: [],
            }

            await async_setup_entry(hass, entry)

        assert hass.services.has_service(DOMAIN, SERVICE_UPDATE_DEVS)

    async def test_platforms_forwarded_when_devices_exist(self, hass: HomeAssistant):
        """Forward platform setup when devices are present."""
        entry = _make_config_entry(hass)

        mock_device = MagicMock()

        with (
            patch("custom_components.vesync.VeSync") as mock_vesync_class,
            patch(
                "custom_components.vesync.async_process_devices"
            ) as mock_process,
            patch.object(
                hass.config_entries,
                "async_forward_entry_setups",
                new=AsyncMock(),
            ) as mock_forward,
        ):
            manager = mock_vesync_class.return_value
            manager.login = MagicMock(return_value=True)
            manager.update = MagicMock()

            mock_process.return_value = {
                VS_SWITCHES: [mock_device],
                VS_FANS: [],
                VS_LIGHTS: [],
                VS_SENSORS: [],
                VS_HUMIDIFIERS: [],
                VS_NUMBERS: [],
                VS_BINARY_SENSORS: [],
                VS_BUTTON: [],
            }

            await async_setup_entry(hass, entry)

        # Verify devices stored in hass.data
        assert mock_device in hass.data[DOMAIN][entry.entry_id][VS_SWITCHES]
        # Verify platform setup was forwarded for switch platform
        mock_forward.assert_called_once()
        forwarded_platforms = mock_forward.call_args[0][1]
        assert "switch" in [str(p) for p in forwarded_platforms]

    async def test_manager_stored_in_hass_data(self, hass: HomeAssistant):
        """Store the VeSync manager in hass.data."""
        entry = _make_config_entry(hass)

        with (
            patch("custom_components.vesync.VeSync") as mock_vesync_class,
            patch(
                "custom_components.vesync.async_process_devices"
            ) as mock_process,
        ):
            manager = mock_vesync_class.return_value
            manager.login = MagicMock(return_value=True)
            manager.update = MagicMock()

            mock_process.return_value = {
                VS_SWITCHES: [],
                VS_FANS: [],
                VS_LIGHTS: [],
                VS_SENSORS: [],
                VS_HUMIDIFIERS: [],
                VS_NUMBERS: [],
                VS_BINARY_SENSORS: [],
                VS_BUTTON: [],
            }

            await async_setup_entry(hass, entry)

        assert hass.data[DOMAIN][entry.entry_id][VS_MANAGER] is manager

    async def test_timezone_passed_to_manager(self, hass: HomeAssistant):
        """Pass the HA timezone to VeSync manager."""
        entry = _make_config_entry(hass)

        with (
            patch("custom_components.vesync.VeSync") as mock_vesync_class,
            patch(
                "custom_components.vesync.async_process_devices"
            ) as mock_process,
        ):
            manager = mock_vesync_class.return_value
            manager.login = MagicMock(return_value=True)
            manager.update = MagicMock()

            mock_process.return_value = {
                VS_SWITCHES: [],
                VS_FANS: [],
                VS_LIGHTS: [],
                VS_SENSORS: [],
                VS_HUMIDIFIERS: [],
                VS_NUMBERS: [],
                VS_BINARY_SENSORS: [],
                VS_BUTTON: [],
            }

            await async_setup_entry(hass, entry)

        # VeSync constructor called with username, password, timezone
        mock_vesync_class.assert_called_once_with(
            "test@example.com",
            "test_password",
            str(hass.config.time_zone),
        )


# ---------------------------------------------------------------------------
# async_unload_entry tests
# ---------------------------------------------------------------------------


class TestAsyncUnloadEntry:
    """Tests for async_unload_entry."""

    async def test_unload_cleans_up_data(self, hass: HomeAssistant):
        """Clean up hass.data on successful unload."""
        entry = _make_config_entry(hass)

        # Prepopulate hass.data as if setup had run
        hass.data[DOMAIN] = {entry.entry_id: {"some": "data"}}

        with patch.object(
            hass.config_entries,
            "async_unload_platforms",
            new=AsyncMock(return_value=True),
        ):
            result = await async_unload_entry(hass, entry)

        assert result is True
        assert entry.entry_id not in hass.data[DOMAIN]

    async def test_unload_failure_preserves_data(self, hass: HomeAssistant):
        """Preserve hass.data when unload fails."""
        entry = _make_config_entry(hass)

        hass.data[DOMAIN] = {entry.entry_id: {"some": "data"}}

        with patch.object(
            hass.config_entries,
            "async_unload_platforms",
            new=AsyncMock(return_value=False),
        ):
            result = await async_unload_entry(hass, entry)

        assert result is False
        assert entry.entry_id in hass.data[DOMAIN]


# ---------------------------------------------------------------------------
# _add_new_devices bug fix verification
# ---------------------------------------------------------------------------


class TestAddNewDevicesBugFix:
    """Tests verifying the _add_new_devices bug fix.

    Previously, _add_new_devices always compared against VS_SWITCHES
    regardless of which platform was being processed. After the fix,
    it correctly uses PLATFORMS[platform] to look up new devices for
    each platform.
    """

    async def test_new_fan_detected_correctly(self, hass: HomeAssistant):
        """Detect a new fan device when processing the fan platform."""
        entry = _make_config_entry(hass)
        new_fan = MagicMock()

        with (
            patch("custom_components.vesync.VeSync") as mock_vesync_class,
            patch(
                "custom_components.vesync.async_process_devices"
            ) as mock_process,
            patch("custom_components.vesync.async_dispatcher_send") as mock_dispatch,
        ):
            manager = mock_vesync_class.return_value
            manager.login = MagicMock(return_value=True)
            manager.update = MagicMock()

            # Initial setup with no devices
            mock_process.return_value = {
                VS_SWITCHES: [],
                VS_FANS: [],
                VS_LIGHTS: [],
                VS_SENSORS: [],
                VS_HUMIDIFIERS: [],
                VS_NUMBERS: [],
                VS_BINARY_SENSORS: [],
                VS_BUTTON: [],
            }

            await async_setup_entry(hass, entry)

            # Now simulate discovering a new fan (but no new switches)
            mock_process.return_value = {
                VS_SWITCHES: [],
                VS_FANS: [new_fan],
                VS_LIGHTS: [],
                VS_SENSORS: [],
                VS_HUMIDIFIERS: [],
                VS_NUMBERS: [],
                VS_BINARY_SENSORS: [],
                VS_BUTTON: [],
            }

            # Call the update_devices service
            await hass.services.async_call(
                DOMAIN, SERVICE_UPDATE_DEVS, blocking=True
            )

        # The new fan should have been detected and dispatched.
        # Before the bug fix, this would fail because the code
        # always compared against VS_SWITCHES (which was empty),
        # rather than VS_FANS.
        fan_dispatched = any(
            VS_FANS in str(call) for call in mock_dispatch.call_args_list
        )
        assert fan_dispatched, (
            "New fan device should be detected and dispatched "
            "via the fans platform, not compared against switches"
        )
