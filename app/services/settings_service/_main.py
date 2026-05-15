import json
import logging
import os
from pathlib import Path

from app.core import settings
from app.core import DEVICES_PATH, EXAMPLE_PATH, FILES_PATH
from app.services import rfid_manager
import asyncio
from typing import Any, Dict, Union
from smartx_rfid.utils import delayed_function
from app.services.tray import tray_manager


class SettingsService:
	def __init__(self):
		self.has_changes: bool = False

	def update_settings(self, data: dict):
		settings.load(data)
		settings.save()
		self.has_changes = True

	def reload_devices(self):
		asyncio.create_task(rfid_manager.devices.cancel_connect_tasks())

	def create_device(self, device_name: str, data: dict) -> tuple[bool, str | None]:
		try:
			Path(DEVICES_PATH).mkdir(parents=True, exist_ok=True)

			device_path = os.path.join(DEVICES_PATH, f'{device_name}.json')

			if os.path.exists(device_path):
				return False, 'Device already exists'

			with open(device_path, 'w', encoding='utf-8') as f:
				json.dump(data, f, indent=4, ensure_ascii=False)

			logging.info(f'Device created: {device_name}')

			self.reload_devices()
			return True, None
		except Exception as e:
			return False, str(e)

	def update_device(self, device_name: str, data: dict) -> tuple[bool, str | None]:
		try:
			device_path = os.path.join(DEVICES_PATH, f'{device_name}.json')

			if not os.path.exists(device_path):
				return False, 'Device does not exist'

			with open(device_path, 'w', encoding='utf-8') as f:
				json.dump(data, f, indent=4, ensure_ascii=False)

			logging.info(f'Device updated: {device_name}')

			self.reload_devices()
			return True, None
		except Exception as e:
			return False, str(e)

	def delete_device(self, device_name: str) -> tuple[bool, str | None]:
		try:
			device_path = os.path.join(DEVICES_PATH, f'{device_name}.json')

			if not os.path.exists(device_path):
				return False, 'Device does not exist'

			os.remove(device_path)
			logging.info(f'Device deleted: {device_name}')

			self.reload_devices()
			return True, None
		except Exception as e:
			return False, str(e)

	def _get_example_config(self) -> dict:
		try:
			config_path = os.path.join(EXAMPLE_PATH, 'config.json')
			if not os.path.exists(config_path):
				return {}

			with open(config_path, 'r', encoding='utf-8') as f:
				data = json.load(f)

			return {key: value for key, value in data.items() if not key.startswith('_')}
		except Exception:
			return {}

	def backup_config(self):
		"""Create a recursive backup dict of JSON files under FILES_PATH.

		Returns a nested dictionary representing the directory tree where
		JSON files are parsed and included. Non-JSON files are ignored.
		"""
		try:
			return self._export_files_backup(FILES_PATH)
		except Exception:
			return {}

	def _export_files_backup(self, root_path: Union[str, Path]) -> Dict[str, Any]:
		"""Recursively scan `root_path` for .json files and return a nested dict.

		- `root_path` may be a string or Path.
		- Only files with suffix `.json` are included.
		- For each JSON file, the parsed JSON object is stored at the file name
		position in the nested dict. If parsing fails, the raw text is stored
		under a dict with keys `_raw` and `_error`.
		"""
		root = Path(root_path)
		result: Dict[str, Any] = {}

		if not root.exists() or not root.is_dir():
			return result

		for p in root.rglob('*.json'):
			try:
				rel = p.relative_to(root).parts
			except Exception:
				# skip files that can't be relativized
				continue

			cur: Dict[str, Any] = result
			for part in rel[:-1]:
				cur = cur.setdefault(part, {})

			filename = rel[-1]
			try:
				with p.open('r', encoding='utf-8') as fh:
					data = json.load(fh)
				cur[filename] = data
			except Exception as e:
				try:
					raw = p.read_text(encoding='utf-8')
				except Exception:
					raw = ''
				cur[filename] = {'_raw': raw, '_error': str(e)}

		return result

	def import_config(self, data: dict, purge: bool = True) -> tuple[bool, str | None]:
		"""Write backup `data` into `FILES_PATH` recursively.

		If `purge` is True (default), delete all existing `.json` files under
		`FILES_PATH` before writing the incoming data. Returns (True, None)
		on success or (False, error_message) on failure.
		"""
		try:

			def _write_node(node: Dict[str, Any], base: Path):
				base.mkdir(parents=True, exist_ok=True)
				for name, value in node.items():
					target = base / name
					if isinstance(value, dict) and not name.lower().endswith('.json'):
						# directory
						_write_node(value, target)
					else:
						# file entry expected (filename.json)
						if isinstance(value, dict) and '_raw' in value:
							raw = value.get('_raw', '')
							target.write_text(raw or '', encoding='utf-8')
						else:
							with target.open('w', encoding='utf-8') as fh:
								json.dump(value, fh, indent=4, ensure_ascii=False)

			root = Path(FILES_PATH)
			# validate incoming data
			if not isinstance(data, dict):
				return False, 'Invalid data for import: expected dict'

			# purge existing json files if requested
			if purge and root.exists() and root.is_dir():
				for existing in root.rglob('*.json'):
					try:
						existing.unlink()
					except Exception:
						# ignore deletion errors but continue
						pass

			_write_node(data, root)

			# mark changes and reload if necessary
			asyncio.create_task(delayed_function(tray_manager.restart_application, 1))

			return True, None
		except Exception as e:
			return False, str(e)
