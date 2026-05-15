import logging

import pytest

from app.services.rfid.integration import Integration
from app.services.rfid import integration as integration_module


def test_integration_skips_indicator_when_beep_is_disabled(monkeypatch):
	class FailingIndicator:
		def __init__(self):
			raise AssertionError('Indicator should not be initialized')

	monkeypatch.setattr(integration_module.settings, 'BEEP', False)
	monkeypatch.setattr(Integration, 'setup_integration', lambda self: None)
	monkeypatch.setattr(integration_module, 'Indicator', FailingIndicator)

	integration = Integration()

	assert integration.indicator is None


@pytest.mark.asyncio
async def test_on_tag_integration_logs_failures_without_raising(monkeypatch, caplog):
	class FailingWebhook:
		async def post_event(self, device, event_type, event_data):
			raise RuntimeError('webhook failure')

	class FailingXtrack:
		async def post(self, tag):
			raise RuntimeError('xtrack failure')

	monkeypatch.setattr(integration_module.settings, 'BEEP', False)
	monkeypatch.setattr(Integration, 'setup_integration', lambda self: None)

	integration = Integration()
	integration.webhook_manager = FailingWebhook()
	integration.webhook_xtrack = FailingXtrack()

	with caplog.at_level(logging.ERROR):
		await integration.on_tag_integration({'device': 'reader-01', 'epc': 'ABC'})

	assert 'webhook failure' in caplog.text
	assert 'xtrack failure' in caplog.text
