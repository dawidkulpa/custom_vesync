"""Shared fixtures for VeSync tests."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from custom_components.vesync.const import DOMAIN


# ---------------------------------------------------------------------------
# Stub out homeassistant.components.dhcp so config_flow.py can be imported
# without the ``aiodiscover`` C-extension dependency.
# ---------------------------------------------------------------------------
if "homeassistant.components.dhcp" not in sys.modules:
    from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

    _dhcp_stub = MagicMock()
    _dhcp_stub.DhcpServiceInfo = DhcpServiceInfo
    sys.modules["homeassistant.components.dhcp"] = _dhcp_stub


# ---------------------------------------------------------------------------
# Global autouse fixture: prevent schedule_update_ha_state from needing hass
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _patch_schedule_update(monkeypatch):
    """Prevent schedule_update_ha_state from requiring a running event loop."""
    from homeassistant.helpers.entity import Entity

    monkeypatch.setattr(
        Entity, "schedule_update_ha_state", lambda self: None
    )


# ---------------------------------------------------------------------------
# Global autouse fixture: ensure the custom integration is loaded instead of
# the bundled homeassistant.components.vesync (which requires a newer pyvesync).
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _ensure_custom_integration(hass):
    """Clear the DATA_CUSTOM_COMPONENTS cache so our custom integration wins."""
    from homeassistant.loader import (
        DATA_CUSTOM_COMPONENTS,
        DATA_INTEGRATIONS,
    )

    # Remove any stale cached empty dict or bundled integration entry
    hass.data.pop(DATA_CUSTOM_COMPONENTS, None)
    hass.data.get(DATA_INTEGRATIONS, {}).pop(DOMAIN, None)


# ---------------------------------------------------------------------------
# Mock device factory helpers
# ---------------------------------------------------------------------------


def _base_device_attrs(
    device_name="TestDevice",
    device_type="ESW15-USA",
    cid="test-cid-123",
    uuid="test-uuid-456",
    connection_status="online",
    device_status="on",
    sub_device_no=None,
    current_firm_version="1.0.0",
):
    """Return a dict with common device attributes."""
    return {
        "device_name": device_name,
        "device_type": device_type,
        "cid": cid,
        "uuid": uuid,
        "connection_status": connection_status,
        "device_status": device_status,
        "sub_device_no": sub_device_no,
        "current_firm_version": current_firm_version,
        "mac_id": "AA:BB:CC:DD:EE:FF",
    }


def _make_mock(attrs, extras=None):
    """Create a MagicMock with given attrs dict applied."""
    mock = MagicMock()
    for k, v in attrs.items():
        setattr(mock, k, v)
    if extras:
        for k, v in extras.items():
            setattr(mock, k, v)
    return mock


# ---------------------------------------------------------------------------
# Individual mock-device fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_outlet_device():
    """Return a mock VeSync outlet device."""
    attrs = _base_device_attrs(
        device_name="TestOutlet",
        device_type="ESW15-USA",
        cid="outlet-cid",
    )
    extras = {
        "power": 15.5,
        "energy_today": 1.2,
        "voltage": 120.0,
        "weekly_energy_total": 8.4,
        "monthly_energy_total": 36.0,
        "yearly_energy_total": 432.0,
        "turn_on": MagicMock(),
        "turn_off": MagicMock(),
        "update": MagicMock(),
        "update_energy": MagicMock(),
        "is_dimmable": MagicMock(return_value=False),
    }
    return _make_mock(attrs, extras)


@pytest.fixture
def mock_bulb_dimmable_device():
    """Return a mock VeSync dimmable bulb device."""
    attrs = _base_device_attrs(
        device_name="TestBulb",
        device_type="ESL100",
        cid="bulb-cid",
    )
    extras = {
        "brightness": 75,
        "turn_on": MagicMock(),
        "turn_off": MagicMock(),
        "set_brightness": MagicMock(),
    }
    return _make_mock(attrs, extras)


@pytest.fixture
def mock_bulb_tunable_device():
    """Return a mock VeSync tunable white bulb device."""
    attrs = _base_device_attrs(
        device_name="TestTunableBulb",
        device_type="ESL100CW",
        cid="tunable-cid",
    )
    extras = {
        "brightness": 80,
        "color_temp_pct": 50,
        "turn_on": MagicMock(),
        "turn_off": MagicMock(),
        "set_brightness": MagicMock(),
        "set_color_temp": MagicMock(),
    }
    return _make_mock(attrs, extras)


@pytest.fixture
def mock_wall_switch_device():
    """Return a mock VeSync wall switch device (non-dimmable)."""
    attrs = _base_device_attrs(
        device_name="TestWallSwitch",
        device_type="ESWL01",
        cid="wall-switch-cid",
    )
    extras = {
        "turn_on": MagicMock(),
        "turn_off": MagicMock(),
        "is_dimmable": MagicMock(return_value=False),
    }
    return _make_mock(attrs, extras)


@pytest.fixture
def mock_dimmer_device():
    """Return a mock VeSync wall dimmer device."""
    attrs = _base_device_attrs(
        device_name="TestDimmer",
        device_type="ESWD16",
        cid="dimmer-cid",
    )
    extras = {
        "brightness": 60,
        "turn_on": MagicMock(),
        "turn_off": MagicMock(),
        "set_brightness": MagicMock(),
        "is_dimmable": MagicMock(return_value=True),
    }
    return _make_mock(attrs, extras)


@pytest.fixture
def mock_fan_device():
    """Return a mock VeSync fan device."""
    attrs = _base_device_attrs(
        device_name="TestFan",
        device_type="LAP-C201S-AUSR",
        cid="fan-cid",
    )
    extras = {
        "fan_level": 2,
        "mode": "manual",
        "speed": 2,
        "is_on": True,
        "details": {"humidity": 45},
        "night_light": None,
        "_config_dict": {
            "module": "VeSyncAirBypass",
            "levels": [1, 2, 3],
            "modes": ["auto", "manual", "sleep"],
        },
        "turn_on": MagicMock(),
        "turn_off": MagicMock(),
        "manual_mode": MagicMock(),
        "auto_mode": MagicMock(),
        "sleep_mode": MagicMock(),
        "turbo_mode": MagicMock(),
        "change_fan_speed": MagicMock(),
        "child_lock_on": MagicMock(),
        "child_lock_off": MagicMock(),
        "turn_on_display": MagicMock(),
        "turn_off_display": MagicMock(),
    }
    return _make_mock(attrs, extras)


@pytest.fixture
def mock_humidifier_device():
    """Return a mock VeSync humidifier device."""
    attrs = _base_device_attrs(
        device_name="TestHumidifier",
        device_type="LUH-D301S-WEU",
        cid="humidifier-cid",
    )
    extras = {
        "enabled": True,
        "mode": "auto",
        "mist_modes": ["auto", "humidity", "manual", "sleep"],
        "details": {
            "mode": "auto",
            "humidity": 55,
            "mist_virtual_level": 3,
            "mist_level": 3,
            "warm_mist_level": 0,
            "water_lacks": False,
            "water_tank_lifted": False,
            "display": True,
            "child_lock": False,
        },
        "config": {
            "auto_target_humidity": 55,
            "automatic_stop": True,
        },
        "_config_dict": {
            "module": "VeSyncHumid200300S",
            "mist_levels": [1, 2, 3, 4, 5, 6, 7, 8, 9],
            "warm_mist_levels": [0, 1, 2, 3],
        },
        "turn_on": MagicMock(return_value=True),
        "turn_off": MagicMock(return_value=True),
        "set_humidity": MagicMock(return_value=True),
        "set_humidity_mode": MagicMock(return_value=True),
        "set_mist_level": MagicMock(),
        "set_warm_level": MagicMock(),
        "set_auto_mode": MagicMock(),
        "set_manual_mode": MagicMock(),
        "automatic_stop_on": MagicMock(),
        "automatic_stop_off": MagicMock(),
        "turn_on_display": MagicMock(),
        "turn_off_display": MagicMock(),
        "child_lock_on": MagicMock(),
        "child_lock_off": MagicMock(),
        "night_light": None,
    }
    return _make_mock(attrs, extras)


@pytest.fixture
def mock_airfryer_device():
    """Return a mock VeSync air fryer device."""
    attrs = _base_device_attrs(
        device_name="TestAirFryer",
        device_type="CS158",
        cid="airfryer-cid",
    )
    extras = {
        "fryer_status": "cooking",
        "cook_set_temp": 200,
        "current_temp": 180,
        "cook_last_time": 10,
        "preheat_last_time": 5,
        "cook_status": "cooking",
        "is_heating": True,
        "is_cooking": True,
        "is_running": True,
        "end": MagicMock(),
        "turn_on": MagicMock(),
        "turn_off": MagicMock(),
    }
    return _make_mock(attrs, extras)


# ---------------------------------------------------------------------------
# Mock VeSync manager fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_vesync_manager(
    mock_outlet_device,
    mock_fan_device,
    mock_bulb_dimmable_device,
    mock_wall_switch_device,
):
    """Return a mock VeSync manager with devices attached."""
    manager = MagicMock()
    manager.account_id = "test-account-id"
    manager.login = MagicMock(return_value=True)
    manager.update = MagicMock()

    manager.outlets = [mock_outlet_device]
    manager.fans = [mock_fan_device]
    manager.bulbs = [mock_bulb_dimmable_device]
    manager.switches = [mock_wall_switch_device]
    manager.kitchen = []

    manager._dev_list = {
        "fans": [mock_fan_device],
        "outlets": [mock_outlet_device],
        "switches": [mock_wall_switch_device],
        "bulbs": [mock_bulb_dimmable_device],
    }

    return manager


@pytest.fixture
def mock_empty_manager():
    """Return a mock VeSync manager with no devices."""
    manager = MagicMock()
    manager.account_id = "test-account-id"
    manager.login = MagicMock(return_value=True)
    manager.update = MagicMock()

    manager.outlets = None
    manager.fans = None
    manager.bulbs = None
    manager.switches = None
    manager.kitchen = None

    manager._dev_list = {
        "fans": [],
        "outlets": [],
        "switches": [],
        "bulbs": [],
    }

    return manager


# ---------------------------------------------------------------------------
# Config entry fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_config_entry():
    """Return a mock config entry for VeSync."""
    from homeassistant.config_entries import ConfigEntry

    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.domain = DOMAIN
    entry.title = "test@example.com"
    entry.data = {
        CONF_USERNAME: "test@example.com",
        CONF_PASSWORD: "test_password",
    }
    entry.options = {}
    entry.unique_id = "test@example.com-test-account-id"
    return entry


# ---------------------------------------------------------------------------
# Coordinator fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_coordinator():
    """Return a mock DataUpdateCoordinator."""
    coordinator = MagicMock()
    coordinator.async_add_listener = MagicMock(return_value=MagicMock())
    return coordinator


# ---------------------------------------------------------------------------
# Patching helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def patch_vesync_login():
    """Patch VeSync.login to succeed."""
    with patch(
        "custom_components.vesync.config_flow.VeSync"
    ) as mock_vesync_class:
        instance = mock_vesync_class.return_value
        instance.login = MagicMock(return_value=True)
        instance.account_id = "test-account-id"
        yield mock_vesync_class


@pytest.fixture
def patch_vesync_login_fail():
    """Patch VeSync.login to fail."""
    with patch(
        "custom_components.vesync.config_flow.VeSync"
    ) as mock_vesync_class:
        instance = mock_vesync_class.return_value
        instance.login = MagicMock(return_value=False)
        instance.account_id = "test-account-id"
        yield mock_vesync_class
