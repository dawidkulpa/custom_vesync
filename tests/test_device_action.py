"""Tests for VeSync device_action module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol

from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_MODE,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from custom_components.vesync.const import DOMAIN
from custom_components.vesync.device_action import (
    async_call_action_from_config,
    async_get_action_capabilities,
    async_get_actions,
)


# ---------------------------------------------------------------------------
# async_get_actions tests
# ---------------------------------------------------------------------------


class TestAsyncGetActions:
    """Tests for async_get_actions."""

    async def test_returns_set_mode_action_for_fan_entity(self, hass: HomeAssistant):
        """Return a set_mode action for fan entities on the device."""
        device_id = "test_device_id"

        # Create a mock entity registry entry for a fan entity
        fan_entry = MagicMock()
        fan_entry.domain = "fan"
        fan_entry.entity_id = "fan.test_fan"

        with (
            patch.object(er, "async_get") as mock_er_get,
            patch.object(
                er, "async_entries_for_device", return_value=[fan_entry]
            ),
            patch(
                "homeassistant.components.device_automation.toggle_entity.async_get_actions",
                new=AsyncMock(return_value=[]),
            ),
        ):
            mock_er_get.return_value = MagicMock()
            actions = await async_get_actions(hass, device_id)

        set_mode_actions = [a for a in actions if a.get(CONF_TYPE) == "set_mode"]
        assert len(set_mode_actions) == 1
        assert set_mode_actions[0][CONF_ENTITY_ID] == "fan.test_fan"
        assert set_mode_actions[0][CONF_DEVICE_ID] == device_id
        assert set_mode_actions[0][CONF_DOMAIN] == DOMAIN

    async def test_skips_non_fan_entities(self, hass: HomeAssistant):
        """Skip entities that are not fans."""
        device_id = "test_device_id"

        switch_entry = MagicMock()
        switch_entry.domain = "switch"
        switch_entry.entity_id = "switch.test_switch"

        with (
            patch.object(er, "async_get") as mock_er_get,
            patch.object(
                er, "async_entries_for_device", return_value=[switch_entry]
            ),
            patch(
                "homeassistant.components.device_automation.toggle_entity.async_get_actions",
                new=AsyncMock(return_value=[]),
            ),
        ):
            mock_er_get.return_value = MagicMock()
            actions = await async_get_actions(hass, device_id)

        set_mode_actions = [a for a in actions if a.get(CONF_TYPE) == "set_mode"]
        assert len(set_mode_actions) == 0

    async def test_includes_toggle_actions(self, hass: HomeAssistant):
        """Include toggle actions from the base toggle_entity helper."""
        device_id = "test_device_id"

        toggle_action = {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_TYPE: "turn_on",
        }

        with (
            patch.object(er, "async_get") as mock_er_get,
            patch.object(
                er, "async_entries_for_device", return_value=[]
            ),
            patch(
                "homeassistant.components.device_automation.toggle_entity.async_get_actions",
                new=AsyncMock(return_value=[toggle_action]),
            ),
        ):
            mock_er_get.return_value = MagicMock()
            actions = await async_get_actions(hass, device_id)

        assert toggle_action in actions


# ---------------------------------------------------------------------------
# async_call_action_from_config tests
# ---------------------------------------------------------------------------


class TestAsyncCallActionFromConfig:
    """Tests for async_call_action_from_config."""

    async def test_set_mode_calls_fan_service(self, hass: HomeAssistant):
        """Call fan.set_preset_mode when action type is set_mode."""
        config = {
            CONF_TYPE: "set_mode",
            CONF_ENTITY_ID: "fan.test_fan",
            ATTR_MODE: "auto",
        }

        calls = []

        async def mock_service(call):
            """Track service calls."""
            calls.append(call)

        hass.services.async_register("fan", "set_preset_mode", mock_service)

        await async_call_action_from_config(hass, config, {}, Context())

        assert len(calls) == 1
        assert calls[0].data[ATTR_ENTITY_ID] == "fan.test_fan"
        assert calls[0].data["preset_mode"] == "auto"

    async def test_non_set_mode_delegates_to_toggle(self, hass: HomeAssistant):
        """Delegate non-set_mode actions to toggle_entity helper."""
        config = {
            CONF_TYPE: "turn_on",
            CONF_ENTITY_ID: "fan.test_fan",
        }

        with patch(
            "custom_components.vesync.device_action.toggle_entity.async_call_action_from_config",
            new=AsyncMock(),
        ) as mock_toggle:
            await async_call_action_from_config(hass, config, {}, Context())

        mock_toggle.assert_called_once()


# ---------------------------------------------------------------------------
# async_get_action_capabilities tests
# ---------------------------------------------------------------------------


class TestAsyncGetActionCapabilities:
    """Tests for async_get_action_capabilities."""

    async def test_set_mode_returns_extra_fields(self, hass: HomeAssistant):
        """Return extra_fields with available modes for set_mode action."""
        config = {
            CONF_TYPE: "set_mode",
            CONF_ENTITY_ID: "fan.test_fan",
        }

        with patch(
            "custom_components.vesync.device_action.get_capability",
            return_value=["auto", "manual", "sleep"],
        ):
            capabilities = await async_get_action_capabilities(hass, config)

        assert "extra_fields" in capabilities
        # The schema should be a voluptuous Schema
        assert isinstance(capabilities["extra_fields"], vol.Schema)

    async def test_non_set_mode_returns_empty(self, hass: HomeAssistant):
        """Return empty dict for non-set_mode actions."""
        config = {
            CONF_TYPE: "turn_on",
            CONF_ENTITY_ID: "fan.test_fan",
        }

        capabilities = await async_get_action_capabilities(hass, config)

        assert capabilities == {}

    async def test_set_mode_handles_missing_capability(self, hass: HomeAssistant):
        """Handle HomeAssistantError when getting capabilities."""
        config = {
            CONF_TYPE: "set_mode",
            CONF_ENTITY_ID: "fan.test_fan",
        }

        with patch(
            "custom_components.vesync.device_action.get_capability",
            side_effect=HomeAssistantError("Entity not found"),
        ):
            capabilities = await async_get_action_capabilities(hass, config)

        assert "extra_fields" in capabilities

    async def test_set_mode_handles_none_capability(self, hass: HomeAssistant):
        """Handle None return from get_capability."""
        config = {
            CONF_TYPE: "set_mode",
            CONF_ENTITY_ID: "fan.test_fan",
        }

        with patch(
            "custom_components.vesync.device_action.get_capability",
            return_value=None,
        ):
            capabilities = await async_get_action_capabilities(hass, config)

        assert "extra_fields" in capabilities
