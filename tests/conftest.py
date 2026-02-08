"""Shared fixtures for VeSync tests."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

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
        "sub_device_no": sub_device_no,
        "current_firm_version": current_firm_version,
        "mac_id": "AA:BB:CC:DD:EE:FF",
    }


def _make_state(connection_status="online", device_status="on", **kwargs):
    """Create a mock state object with the given attributes."""
    state = MagicMock()
    state.connection_status = connection_status
    state.device_status = device_status
    for k, v in kwargs.items():
        setattr(state, k, v)
    return state


def _make_mock(attrs, extras=None, state=None):
    """Create a MagicMock with given attrs dict applied."""
    mock = MagicMock()
    for k, v in attrs.items():
        setattr(mock, k, v)
    if extras:
        for k, v in extras.items():
            setattr(mock, k, v)
    if state is not None:
        mock.state = state
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
    state = _make_state(
        power=15.5,
        voltage=120.0,
        energy=1.2,
        weekly_history=8.4,
        monthly_history=36.0,
        yearly_history=432.0,
    )
    extras = {
        "product_type": "outlet",
        "turn_on": AsyncMock(),
        "turn_off": AsyncMock(),
        "update": AsyncMock(),
        "update_energy": AsyncMock(),
    }
    return _make_mock(attrs, extras, state=state)


@pytest.fixture
def mock_bulb_dimmable_device():
    """Return a mock VeSync dimmable bulb device."""
    attrs = _base_device_attrs(
        device_name="TestBulb",
        device_type="ESL100",
        cid="bulb-cid",
    )
    state = _make_state(
        brightness=75,
    )
    extras = {
        "product_type": "bulb",
        "turn_on": AsyncMock(),
        "turn_off": AsyncMock(),
        "set_brightness": AsyncMock(),
    }
    return _make_mock(attrs, extras, state=state)


@pytest.fixture
def mock_bulb_tunable_device():
    """Return a mock VeSync tunable white bulb device."""
    attrs = _base_device_attrs(
        device_name="TestTunableBulb",
        device_type="ESL100CW",
        cid="tunable-cid",
    )
    state = _make_state(
        brightness=80,
        color_temp=50,
    )
    extras = {
        "product_type": "bulb",
        "turn_on": AsyncMock(),
        "turn_off": AsyncMock(),
        "set_brightness": AsyncMock(),
        "set_color_temp": AsyncMock(),
    }
    return _make_mock(attrs, extras, state=state)


@pytest.fixture
def mock_wall_switch_device():
    """Return a mock VeSync wall switch device (non-dimmable)."""
    attrs = _base_device_attrs(
        device_name="TestWallSwitch",
        device_type="ESWL01",
        cid="wall-switch-cid",
    )
    state = _make_state()
    extras = {
        "product_type": "switch",
        "supports_dimmable": False,
        "turn_on": AsyncMock(),
        "turn_off": AsyncMock(),
    }
    return _make_mock(attrs, extras, state=state)


@pytest.fixture
def mock_dimmer_device():
    """Return a mock VeSync wall dimmer device."""
    attrs = _base_device_attrs(
        device_name="TestDimmer",
        device_type="ESWD16",
        cid="dimmer-cid",
    )
    state = _make_state(
        brightness=60,
    )
    extras = {
        "product_type": "switch",
        "supports_dimmable": True,
        "turn_on": AsyncMock(),
        "turn_off": AsyncMock(),
        "set_brightness": AsyncMock(),
    }
    return _make_mock(attrs, extras, state=state)


@pytest.fixture
def mock_fan_device():
    """Return a mock VeSync fan device."""
    attrs = _base_device_attrs(
        device_name="TestFan",
        device_type="LAP-C201S-AUSR",
        cid="fan-cid",
    )
    state = _make_state(
        fan_level=2,
        mode="manual",
        humidity=45,
    )
    state.to_dict = MagicMock(return_value={"humidity": 45, "fan_level": 2, "mode": "manual"})
    extras = {
        "product_type": "fan",
        "is_on": True,
        "fan_levels": [1, 2, 3],
        "modes": ["auto", "manual", "sleep"],
        "supports_nightlight": False,
        "supports_nightlight_brightness": False,
        "turn_on": AsyncMock(),
        "turn_off": AsyncMock(),
        "set_manual_mode": AsyncMock(),
        "set_auto_mode": AsyncMock(),
        "set_sleep_mode": AsyncMock(),
        "set_turbo_mode": AsyncMock(),
        "set_fan_speed": AsyncMock(),
        "turn_on_child_lock": AsyncMock(),
        "turn_off_child_lock": AsyncMock(),
        "turn_on_display": AsyncMock(),
        "turn_off_display": AsyncMock(),
    }
    return _make_mock(attrs, extras, state=state)


@pytest.fixture
def mock_humidifier_device():
    """Return a mock VeSync humidifier device."""
    attrs = _base_device_attrs(
        device_name="TestHumidifier",
        device_type="LUH-D301S-WEU",
        cid="humidifier-cid",
    )
    state = _make_state(
        mode="auto",
        humidity=55,
        mist_virtual_level=3,
        mist_level=3,
        warm_mist_level=0,
        water_lacks=False,
        water_tank_lifted=False,
        display_status=True,
        child_lock=False,
        auto_target_humidity=55,
        automatic_stop=True,
    )
    state.to_dict = MagicMock(return_value={
        "mode": "auto",
        "humidity": 55,
        "mist_virtual_level": 3,
        "mist_level": 3,
        "warm_mist_level": 0,
        "water_lacks": False,
        "water_tank_lifted": False,
        "display_status": True,
        "child_lock": False,
        "auto_target_humidity": 55,
        "automatic_stop": True,
    })
    extras = {
        "product_type": "humidifier",
        "is_on": True,
        "mist_modes": {"auto": "auto", "humidity": "humidity", "manual": "manual", "sleep": "sleep"},
        "mist_levels": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "warm_mist_levels": [0, 1, 2, 3],
        "supports_nightlight": False,
        "supports_nightlight_brightness": False,
        "turn_on": AsyncMock(return_value=True),
        "turn_off": AsyncMock(return_value=True),
        "set_humidity": AsyncMock(return_value=True),
        "set_mode": AsyncMock(return_value=True),
        "set_mist_level": AsyncMock(),
        "set_warm_level": AsyncMock(),
        "set_auto_mode": AsyncMock(),
        "set_manual_mode": AsyncMock(),
        "turn_on_automatic_stop": AsyncMock(),
        "turn_off_automatic_stop": AsyncMock(),
        "turn_on_display": AsyncMock(),
        "turn_off_display": AsyncMock(),
        "turn_on_child_lock": AsyncMock(),
        "turn_off_child_lock": AsyncMock(),
    }
    return _make_mock(attrs, extras, state=state)


@pytest.fixture
def mock_airfryer_device():
    """Return a mock VeSync air fryer device."""
    attrs = _base_device_attrs(
        device_name="TestAirFryer",
        device_type="CS158",
        cid="airfryer-cid",
    )
    state = _make_state(
        cook_set_temp=200,
        current_temp=180,
        cook_last_time=10,
        preheat_last_time=5,
        cook_status="cooking",
        is_heating=True,
        is_cooking=True,
        is_running=True,
    )
    extras = {
        "product_type": "airfryer",
        "end": AsyncMock(),
        "turn_on": AsyncMock(),
        "turn_off": AsyncMock(),
    }
    return _make_mock(attrs, extras, state=state)


# ---------------------------------------------------------------------------
# Mock VeSync manager fixture
# ---------------------------------------------------------------------------


def _make_manager_devices(
    outlets=None,
    fans=None,
    bulbs=None,
    switches=None,
    air_fryers=None,
    humidifiers=None,
    air_purifiers=None,
):
    """Create a mock manager.devices object."""
    devices = MagicMock()
    devices.outlets = outlets or []
    devices.fans = fans or []
    devices.bulbs = bulbs or []
    devices.switches = switches or []
    devices.air_fryers = air_fryers or []
    devices.humidifiers = humidifiers or []
    devices.air_purifiers = air_purifiers or []

    # Make devices iterable (used for logging in async_process_devices)
    all_devices = (
        devices.outlets
        + devices.fans
        + devices.bulbs
        + devices.switches
        + devices.air_fryers
        + devices.humidifiers
        + devices.air_purifiers
    )
    devices.__iter__ = MagicMock(return_value=iter(all_devices))
    return devices


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
    manager.login = AsyncMock(return_value=True)
    manager.update = AsyncMock()
    manager.__aenter__ = AsyncMock(return_value=manager)
    manager.__aexit__ = AsyncMock(return_value=False)

    manager.devices = _make_manager_devices(
        outlets=[mock_outlet_device],
        fans=[mock_fan_device],
        bulbs=[mock_bulb_dimmable_device],
        switches=[mock_wall_switch_device],
    )

    return manager


@pytest.fixture
def mock_empty_manager():
    """Return a mock VeSync manager with no devices."""
    manager = MagicMock()
    manager.account_id = "test-account-id"
    manager.login = AsyncMock(return_value=True)
    manager.update = AsyncMock()
    manager.__aenter__ = AsyncMock(return_value=manager)
    manager.__aexit__ = AsyncMock(return_value=False)

    manager.devices = _make_manager_devices()

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
        instance = MagicMock()
        instance.login = AsyncMock(return_value=True)
        instance.account_id = "test-account-id"
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        mock_vesync_class.return_value = instance
        yield mock_vesync_class


@pytest.fixture
def patch_vesync_login_fail():
    """Patch VeSync.login to fail."""
    with patch(
        "custom_components.vesync.config_flow.VeSync"
    ) as mock_vesync_class:
        instance = MagicMock()
        instance.login = AsyncMock(return_value=False)
        instance.account_id = "test-account-id"
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        mock_vesync_class.return_value = instance
        yield mock_vesync_class
