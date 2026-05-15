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
		self.groups = {
			'A': {
				'antennas': [1, 2],
				'state': 'idle',
				'activity_token': 0,
				'reset_task': None,
				'active_positions': {
					1: False,
					2: False,
				},
			},
			'B': {
				'antennas': [3, 4],
				'state': 'idle',
				'activity_token': 0,
				'reset_task': None,
				'active_positions': {
					1: False,
					2: False,
				},
			},
		}
		self.sensor_mapping = {
			's0': {'group': 'A', 'position': 1},
			's1': {'group': 'A', 'position': 2},
			's2': {'group': 'B', 'position': 1},
			's3': {'group': 'B', 'position': 2},
		}
		self.sensors_states = {
			's0': False,
			's1': False,
			's2': False,
			's3': False,
		}

	# [ EVENTS ]
	def on_event(self, name: str, event_type: str, event_data):
		if isinstance(event_data, str) and event_data.startswith('#laser_sensors:'):
			data = event_data.split(':', 1)[1]
			self.treat_sensor_event(name, data)
			return
		logging.info(f'[ EVENT ] {name} - {event_type}: {event_data}')
		# asyncio.create_task(
		# 	self.integration.on_event_integration(
		# 		name=name, event_type=event_type, event_data=event_data
		# 	)
		# )

	# [ Reading Events ]
	def on_start(self, device: str):
		pass

	def on_stop(self, device: str):
		pass

	# [ Tag Events ]
	def on_new_tag(self, name: str, tag: dict):
		logging.info(f'[ TAG ] {name} - {tag}')
		tag['passed'] = 'idle'
		self.define_tag_state(tag)
		# asyncio.create_task(self.integration.on_tag_integration(tag=tag))

	def on_existing_tag(self, name: str, tag: dict):
		# if settings.ALWAYS_SEND:
		# 	asyncio.create_task(self.integration.on_tag_integration(tag=tag))
		self.define_tag_state(tag)

	def define_tag_state(self, tag: dict):
		if not tag.get('passed') == 'idle':
			return
		ant = tag.get('ant')
		a_group = self.groups.get('A').get('antennas')
		b_group = self.groups.get('B').get('antennas')
		if ant in a_group:
			a_state = self.groups.get('A').get('state')
			if a_state == 'idle':
				return
			tag['passed'] = a_state
		elif ant in b_group:
			b_state = self.groups.get('B').get('state')
			if b_state == 'idle':
				return
			tag['passed'] = b_state

	# [ Sensor Events ]
	def treat_sensor_event(self, name: str, data: str):
		# DECODE DATA
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

			self.sensors_states[sensor] = value

			# UPDATE GROUP STATE
			sensor_data = self.sensor_mapping.get(sensor)
			if sensor_data is None:
				logging.warning(f'Unknown sensor: {sensor}')
				continue
			asyncio.create_task(
				self.process_group_sensor_event(
					sensor_data.get('group'),
					sensor_data.get('position'),
					value,
				)
			)

	def set_group_state(self, group_name: str, state: str):
		group = self.groups.get(group_name)
		if group is None:
			logging.warning(f'Unknown group: {group_name}')
			return

		previous_state = group.get('state', 'idle')
		if previous_state == state:
			return

		group['state'] = state
		logging.info(f'Group {group_name} state changed: {previous_state} -> {state}')
		# start/stop reading based on state
		if (
			self.groups.get('A').get('state') == 'idle'
			and self.groups.get('B').get('state') == 'idle'
		):
			asyncio.create_task(self.devices.stop_inventory_all())
		else:
			asyncio.create_task(self.devices.start_inventory_all())

	async def process_group_sensor_event(self, group_name: str, position: int, is_active: bool):
		if group_name not in self.groups:
			logging.warning(f'Unknown group: {group_name}')
			return
		group = self.groups[group_name]
		active_positions = group.get('active_positions', {})
		was_all_inactive = not any(active_positions.values())
		active_positions[position] = is_active

		if is_active and group.get('state') == 'idle':
			# Fora de idle o grupo nao muda para in/out; so pode voltar para idle.
			next_state = 'in' if position == 1 else 'out'
			self.set_group_state(group_name, next_state)

		all_inactive = not any(active_positions.values())

		reset_task = group.get('reset_task')

		if not all_inactive:
			if reset_task and not reset_task.done():
				reset_task.cancel()
			group['reset_task'] = None
			return

		# Se ja estava com todos sensores inativos, mantem o timer atual sem reiniciar.
		if was_all_inactive and reset_task and not reset_task.done():
			return

		group['activity_token'] += 1
		token = group['activity_token']

		if reset_task and not reset_task.done():
			reset_task.cancel()

		group['reset_task'] = asyncio.create_task(
			self._set_group_idle_after_timeout(group_name, token)
		)

	async def _set_group_idle_after_timeout(self, group_name: str, token: int):
		group = self.groups.get(group_name)
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

		self.set_group_state(group_name, 'idle')
		group['reset_task'] = None

	def get_summary(self):
		groups_summary = {}
		for group_name, group_data in self.groups.items():
			groups_summary[group_name] = {
				'antennas': group_data.get('antennas', []),
				'state': group_data.get('state', 'idle'),
				'active_positions': group_data.get('active_positions', {}),
			}

		return {
			'groups': groups_summary,
			'sensors': self.sensors_states,
		}
