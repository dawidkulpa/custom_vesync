"""Provides diagnostics for VeSync."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

# from .common import is_humidifier
# from .const import DOMAIN

TO_REDACT = {"cid", "uuid", "mac_id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    # data = hass.data[DOMAIN][entry.entry_id]
    devices = {}

    # for device in data["manager"].devices:
    #     t = device.product_type or "unknown"
    #     devices = {
    #         **devices,
    #         **{t: [{k: v for k, v in device.__dict__.items() if k != "manager"}]},
    #     }
    return async_redact_data(devices, TO_REDACT)
