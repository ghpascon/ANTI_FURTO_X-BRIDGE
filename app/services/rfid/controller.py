"""
Docstring for app.services.rfid.controller
This module will be used for custom logic.
"""

from smartx_rfid.devices import DeviceManager
from smartx_rfid.utils import TagList
from .integration import Integration
import asyncio
from app.core import settings
import logging


class Controller:
	def __init__(self, devices: DeviceManager, tags: TagList, integration: Integration):
		self.tags = tags
		self.devices = devices
		self.integration = integration
		# Estados por device
		self.devices_states = {}
		# Mapping global
		self.sensor_mapping = {
			's0': {'group': 'A', 'position': 1},
			's1': {'group': 'A', 'position': 2},
			's2': {'group': 'B', 'position': 1},
			's3': {'group': 'B', 'position': 2},
		}

	def _get_or_create_device_state(self, name):
		if name not in self.devices_states:
			self.devices_states[name] = {
				'inventory_running': False,
				'groups': {
					'A': {
						'antennas': [1, 2],
						'state': 'idle',
						'activity_token': 0,
						'reset_task': None,
						'active_positions': {1: False, 2: False},
					},
					'B': {
						'antennas': [3, 4],
						'state': 'idle',
						'activity_token': 0,
						'reset_task': None,
						'active_positions': {1: False, 2: False},
					},
				},
				'sensors_states': {
					's0': False,
					's1': False,
					's2': False,
					's3': False,
				},
			}
		return self.devices_states[name]

	# [ EVENTS ]
	def on_event(self, name: str, event_type: str, event_data):
		if isinstance(event_data, str) and event_data.startswith('#laser_sensors:'):
			data = event_data.split(':', 1)[1]
			self.treat_sensor_event(name, data)
			return
		if event_data == '#pong':
			return
		logging.info(f'[ EVENT ] {name} - {event_type}: {event_data}')
		# asyncio.create_task(
		# 	self.integration.on_event_integration(
		# 		name=name, event_type=event_type, event_data=event_data
		# 	)
		# )

	# [ Reading Events ]
	def on_start(self, name: str):
		logging.info(f'[ START ] {name}')
		# self.tags.remove_tags_by_device(device=name)

	def on_stop(self, name: str):
		logging.info(f'[ STOP ] {name}')

	def start_reading_device(self, device_name: str):
		asyncio.create_task(self.devices.start_inventory(name=device_name))

	def stop_reading_device(self, device_name: str):
		asyncio.create_task(self.devices.stop_inventory(name=device_name))

	def _sync_device_inventory_state(self, device_name: str):
		device_state = self._get_or_create_device_state(device_name)
		groups = device_state.get('groups', {})
		has_active_group = any(group.get('state') != 'idle' for group in groups.values())
		is_running = device_state.get('inventory_running', False)

		if has_active_group and not is_running:
			self.start_reading_device(device_name)
			device_state['inventory_running'] = True
			logging.info(f'Device {device_name} inventory: started')
		elif not has_active_group and is_running:
			self.stop_reading_device(device_name)
			device_state['inventory_running'] = False
			logging.info(f'Device {device_name} inventory: stopped')

	# [ Tag Events ]
	def on_new_tag(self, name: str, tag: dict):
		logging.info(f'[ TAG ] {name} - {tag}')
		tag['passed'] = 'idle'
		self.define_tag_state(name, tag)
		# asyncio.create_task(self.integration.on_tag_integration(tag=tag))

	def on_existing_tag(self, name: str, tag: dict):
		# if settings.ALWAYS_SEND:
		#     asyncio.create_task(self.integration.on_tag_integration(tag=tag))
		self.define_tag_state(name, tag)

	def define_tag_state(self, name: str, tag: dict):
		if not tag.get('passed') == 'idle':
			return
		ant = tag.get('ant')
		device_state = self._get_or_create_device_state(name)
		a_group = device_state['groups'].get('A').get('antennas')
		b_group = device_state['groups'].get('B').get('antennas')
		if ant in a_group:
			a_state = device_state['groups'].get('A').get('state')
			if a_state == 'idle':
				return
			tag['passed'] = a_state
		elif ant in b_group:
			b_state = device_state['groups'].get('B').get('state')
			if b_state == 'idle':
				return
			tag['passed'] = b_state

	# [ Sensor Events ]
	def treat_sensor_event(self, name: str, data: str):
		device_state = self._get_or_create_device_state(name)
		sensor_info = data.split(';')
		for info in sensor_info:
			if ':' not in info:
				logging.warning(f'Invalid sensor payload: {info}')
				continue

			sensor, value = info.split(':')
			try:
				value = int(value) < settings.DISTANCE_THRESHOLD
			except ValueError:
				value = False

			device_state['sensors_states'][sensor] = value

			# logging.info(f'Device {name} - Sensor {sensor} value: {value}')

			# UPDATE GROUP STATE
			sensor_data = self.sensor_mapping.get(sensor)
			if sensor_data is None:
				logging.warning(f'Unknown sensor: {sensor}')
				continue
			asyncio.create_task(
				self.process_group_sensor_event(
					name,
					sensor_data.get('group'),
					sensor_data.get('position'),
					value,
				)
			)

	def set_group_state(self, device_name: str, group_name: str, state: str):
		device_state = self._get_or_create_device_state(device_name)
		group = device_state['groups'].get(group_name)
		if group is None:
			logging.warning(f'Unknown group: {group_name} for device {device_name}')
			return

		previous_state = group.get('state', 'idle')
		if previous_state == state:
			return

		group['state'] = state
		logging.info(
			f'Device {device_name} - Group {group_name} state changed: {previous_state} -> {state}'
		)
		self._sync_device_inventory_state(device_name)

	async def process_group_sensor_event(
		self, device_name: str, group_name: str, position: int, is_active: bool
	):
		device_state = self._get_or_create_device_state(device_name)
		if group_name not in device_state['groups']:
			logging.warning(f'Unknown group: {group_name} for device {device_name}')
			return
		group = device_state['groups'][group_name]
		active_positions = group.get('active_positions', {})
		was_all_inactive = not any(active_positions.values())
		active_positions[position] = is_active

		if is_active and group.get('state') == 'idle':
			next_state = 'in' if position == 1 else 'out'
			self.set_group_state(device_name, group_name, next_state)

		all_inactive = not any(active_positions.values())

		reset_task = group.get('reset_task')

		if not all_inactive:
			if reset_task and not reset_task.done():
				reset_task.cancel()
			group['reset_task'] = None
			return

		if was_all_inactive and reset_task and not reset_task.done():
			return

		group['activity_token'] += 1
		token = group['activity_token']

		if reset_task and not reset_task.done():
			reset_task.cancel()

		group['reset_task'] = asyncio.create_task(
			self._set_group_idle_after_timeout(device_name, group_name, token)
		)

	async def _set_group_idle_after_timeout(self, device_name: str, group_name: str, token: int):
		device_state = self._get_or_create_device_state(device_name)
		group = device_state['groups'].get(group_name)
		if group is None:
			return

		try:
			await asyncio.sleep(settings.SENSOR_IDLE_TIMEOUT)
		except asyncio.CancelledError:
			return

		if group.get('activity_token') != token:
			return

		if any(group.get('active_positions', {}).values()):
			return

		self.set_group_state(device_name, group_name, 'idle')
		group['reset_task'] = None

	def get_summary(self):
		# Retorna o status de todos os devices
		summary = {}
		for device_name, device_state in self.devices_states.items():
			groups_summary = {}
			for group_name, group_data in device_state['groups'].items():
				groups_summary[group_name] = {
					'antennas': group_data.get('antennas', []),
					'state': group_data.get('state', 'idle'),
					'active_positions': group_data.get('active_positions', {}),
				}
			summary[device_name] = {
				'groups': groups_summary,
				'sensors': device_state['sensors_states'],
			}
		return summary
