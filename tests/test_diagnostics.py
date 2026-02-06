"""Tests for VeSync diagnostics."""

from custom_components.vesync.diagnostics import (
    TO_REDACT,
    async_get_config_entry_diagnostics,
)


class TestDiagnostics:
    """Tests for diagnostics module."""

    def test_redact_fields_defined(self):
        """Ensure sensitive fields are in the redaction set."""
        assert "cid" in TO_REDACT
        assert "uuid" in TO_REDACT
        assert "mac_id" in TO_REDACT

    async def test_returns_empty_redacted_data(self, hass, mock_config_entry):
        """Return empty redacted data (implementation is mostly stubbed)."""
        result = await async_get_config_entry_diagnostics(hass, mock_config_entry)
        # Currently returns an empty dict since the implementation is commented out
        assert isinstance(result, dict)
