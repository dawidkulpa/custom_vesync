"""Tests for VeSync config flow."""

from unittest.mock import MagicMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from custom_components.vesync.const import DOMAIN

# Eagerly import config_flow so patch targets resolve correctly.
# The dhcp stub is already set up by conftest.py.
import custom_components.vesync.config_flow  # noqa: E402, F401


class TestConfigFlow:
    """Tests for VeSyncFlowHandler."""

    async def test_show_form_on_empty_input(self, hass: HomeAssistant):
        """Show the user form when no input is provided."""
        with patch(
            "custom_components.vesync.config_flow.VeSync"
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

    async def test_successful_login_creates_entry(
        self, hass: HomeAssistant
    ):
        """Create a config entry on successful login."""
        with patch(
            "custom_components.vesync.config_flow.VeSync"
        ) as mock_vesync_class:
            instance = mock_vesync_class.return_value
            instance.login = MagicMock(return_value=True)
            instance.account_id = "test-account-id"

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            assert result["type"] == FlowResultType.FORM

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_USERNAME: "test@example.com", CONF_PASSWORD: "secret"},
            )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "test@example.com"
        assert result["data"][CONF_USERNAME] == "test@example.com"
        assert result["data"][CONF_PASSWORD] == "secret"

    async def test_invalid_auth_shows_error(
        self, hass: HomeAssistant
    ):
        """Show error when login fails."""
        with patch(
            "custom_components.vesync.config_flow.VeSync"
        ) as mock_vesync_class:
            instance = mock_vesync_class.return_value
            instance.login = MagicMock(return_value=False)
            instance.account_id = "test-account-id"

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_USERNAME: "bad@example.com", CONF_PASSWORD: "wrong"},
            )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}

    async def test_duplicate_entry_aborted(
        self, hass: HomeAssistant
    ):
        """Abort if an entry already exists."""
        with patch(
            "custom_components.vesync.config_flow.VeSync"
        ) as mock_vesync_class:
            instance = mock_vesync_class.return_value
            instance.login = MagicMock(return_value=True)
            instance.account_id = "test-account-id"

            # Create first entry
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_USERNAME: "test@example.com", CONF_PASSWORD: "secret"},
            )

            # Try to create a second entry
            result2 = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
        assert result2["type"] == FlowResultType.ABORT
        assert result2["reason"] == "single_instance_allowed"

    async def test_dhcp_discovery_triggers_user_step(
        self, hass: HomeAssistant
    ):
        """Trigger the user step when DHCP discovers a Levoit device."""
        with patch(
            "custom_components.vesync.config_flow.VeSync"
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_DHCP},
                data=DhcpServiceInfo(
                    hostname="levoit-test",
                    ip="192.168.1.100",
                    macaddress="aabbccddeeff",
                ),
            )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
