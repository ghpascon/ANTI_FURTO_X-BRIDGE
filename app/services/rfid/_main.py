import logging
from smartx_rfid.devices import DeviceManager
from smartx_rfid.utils import TagList
from .integration import Integration
from app.core import settings
from .controller import Controller


class RfidManager:
	def __init__(self, devices_path: str, example_path: str = ''):
		logging.info('Initializing RfidManager')

		# TAGS
		self.tags = TagList(unique_identifier='tid', prefix=settings.TAG_PREFIX)

		# connect to devices
		self.devices = DeviceManager(
			devices_path=devices_path, example_path=example_path, event_func=self.on_event
		)

		# INTEGRATION
		self.integration = Integration()

		# CONTROLLER
		self.controller = Controller(
			devices=self.devices, tags=self.tags, integration=self.integration
		)

		logging.info(f"{'='*20} RfidManager initialized {'='*20}")

	def handle_r700_event(self, events: list):
		for event in events:
			event_type = event.get('eventType')
			device = event.get('hostname', 'unknown')
			if event_type == 'tagInventory':
				tag_data = event.get('tagInventoryEvent')
				if tag_data is not None:
					current_tag = {
						'epc': tag_data.get('epcHex'),
						'tid': tag_data.get('tidHex'),
						'ant': tag_data.get('antennaPort'),
						'rssi': int(tag_data.get('peakRssiCdbm', 0) / 100),
					}
					self.on_tag(name=device, tag_data=current_tag)
			elif event_type == 'inventoryStatus':
				event_data = event.get('inventoryStatusEvent')
				if event_data is not None:
					self.on_event(
						name=device,
						event_type='reading',
						event_data=event_data.get('inventoryStatus') == 'running',
					)

	# ===== EVENTS =====
	def on_event(self, name: str, event_type: str, event_data):
		if event_type == 'tag':
			self.on_tag(name=name, tag_data=event_data)
		else:
			if event_type == 'reading':
				self.on_start(name=name) if event_data else self.on_stop(name=name)

			self.controller.on_event(name=name, event_type=event_type, event_data=event_data)

	def on_tag(self, name: str, tag_data: dict):
		new_tag, tag = self.tags.add(tag_data, device=name)

		# NEW TAG
		if new_tag:
			self.controller.on_new_tag(name=name, tag=tag)

		# EXISTING TAG
		elif tag is not None:
			self.controller.on_existing_tag(name=name, tag=tag)
		return new_tag, tag

	def on_start(self, name: str):
		logging.info(f'[ START ] {name}')
		self.tags.remove_tags_by_device(device=name)
		self.controller.on_start(device=name)

	def on_stop(self, name: str):
		logging.info(f'[ STOP ] {name}')
		self.controller.on_stop(device=name)

	# [ X-SCAN]
	def on_xscan_event(self, device_name: str, event_type: str, event_data):
		# inventory event with tags
		logging.info(
			f'Received X-SCAN event from device {device_name}: {event_type} - {event_data}'
		)
		if event_type == 'inventory':
			for tag in event_data.get('tags', []):
				new_tag, tag_data = self.on_tag(
					name=device_name,
					tag_data={
						'epc': tag.get('epc'),
						'tid': tag.get('tid'),
						'ant': tag.get('antenna', 1),
						'rssi': tag.get('rssi'),
					},
				)
				if tag_data:
					tag_data['count'] += (
						tag.get('read_count', 1) - 1
					)  # Adjust count based on read_count
		else:
			self.on_event(name=device_name, event_type=event_type, event_data=event_data)
