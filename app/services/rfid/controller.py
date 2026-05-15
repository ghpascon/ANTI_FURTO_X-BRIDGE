"""
Docstring for app.services.rfid.controller
This module will be used for custom logic.
"""

from smartx_rfid.devices import DeviceManager
from smartx_rfid.utils import TagList
from .integration import Integration
import asyncio
from app.core import settings


class Controller:
	def __init__(self, devices: DeviceManager, tags: TagList, integration: Integration):
		self.tags = tags
		self.devices = devices
		self.integration = integration

	# [ EVENTS ]
	def on_event(self, name: str, event_type: str, event_data):
		asyncio.create_task(
			self.integration.on_event_integration(
				name=name, event_type=event_type, event_data=event_data
			)
		)

	# [ Reading Events ]
	def on_start(self, device: str):
		pass

	def on_stop(self, device: str):
		pass

	# [ Tag Events ]
	def on_new_tag(self, tag: dict):
		asyncio.create_task(self.integration.on_tag_integration(tag=tag))

	def on_existing_tag(self, tag: dict):
		if settings.ALWAYS_SEND:
			asyncio.create_task(self.integration.on_tag_integration(tag=tag))
