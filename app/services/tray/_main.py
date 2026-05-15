import platform
from pathlib import Path
import subprocess
from threading import Thread
import time
import os
import asyncio
import sys
import webbrowser

try:
	import pystray
	from PIL import Image, ImageDraw

	TRAY_AVAILABLE = True
except ImportError:
	TRAY_AVAILABLE = False

from app.core import settings
from app.services import rfid_manager


class TrayManager:
	"""System tray manager for Windows"""

	def __init__(self, app_name: str, icon_path: str | None = None):
		self.app_name = app_name
		self.icon_path = icon_path
		self._icon = None

		# Vars
		self.title = f'SMARTX - {self.app_name}'

		if TRAY_AVAILABLE and platform.system() == 'Windows':
			self._setup_tray()
			Thread(target=self._update_loop, daemon=True).start()

	def _setup_tray(self):
		# Default icon
		if self.icon_path and Path(self.icon_path).exists():
			icon_image = Image.open(self.icon_path)
		else:
			icon_image = self._create_default_icon()

		# Build initial menu
		self._icon = pystray.Icon(self.app_name, icon_image, self.app_name)
		self._build_menu()

		# Run tray in separate thread
		Thread(target=self._icon.run, daemon=True).start()

	def _build_menu(self):
		"""Rebuilds the tray menu"""
		widgets = []

		# Title
		widgets.append(pystray.MenuItem(lambda text: self.title, lambda: None, enabled=False))

		# Open browser
		widgets.append(pystray.MenuItem('Open Browser', self._open_browser))

		# Total tags
		widgets.append(
			pystray.MenuItem(
				lambda text: f'Total Tags: {len(rfid_manager.tags)}',
				lambda: None,
				enabled=False,
			)
		)
		widgets.append(pystray.Menu.SEPARATOR)

		# Devices submenu
		devices_menu = self._get_devices_submenu()
		widgets.append(
			pystray.MenuItem('Devices', devices_menu)
		)  # <-- submenu como segundo argumento

		widgets.append(pystray.Menu.SEPARATOR)

		# Restart
		widgets.append(pystray.MenuItem('Restart', self.restart_application))
		# Exit
		widgets.append(pystray.MenuItem('Exit', self.exit_application))

		self._icon.menu = pystray.Menu(*widgets)

	def _get_devices_submenu(self):
		"""Generate devices submenu dynamically"""
		devices = rfid_manager.devices.get_device_info()

		if not devices:
			return pystray.Menu(pystray.MenuItem('None', lambda: None, enabled=False))

		items = []
		for device in devices:
			name = device.get('name', 'Unknown')
			device_type = device.get('device_type', 'Unknown')
			connected = device.get('is_connected', False)
			reading = device.get('is_reading', False)

			# Create wrapper functions for async calls
			def make_start_inventory(device_name):
				def start():
					asyncio.run(rfid_manager.devices.start_inventory(device_name))

				return start

			def make_stop_inventory(device_name):
				def stop():
					asyncio.run(rfid_manager.devices.stop_inventory(device_name))

				return stop

			submenu = pystray.Menu(
				pystray.MenuItem(f'Type: {device_type}', lambda: None, enabled=False),
				pystray.MenuItem(
					f"Connected: {'Yes' if connected else 'No'}", lambda: None, enabled=False
				),
				pystray.MenuItem(
					f"Reading: {'Yes' if reading else 'No'}", lambda: None, enabled=False
				),
				pystray.Menu.SEPARATOR,
				pystray.MenuItem('Start Inventory', make_start_inventory(name)),
				pystray.MenuItem('Stop Inventory', make_stop_inventory(name)),
			)

			items.append(pystray.MenuItem(name, submenu))

		return pystray.Menu(*items)

	def _update_loop(self):
		"""Update menu every second"""
		while True:
			if self._icon:
				self._build_menu()
				self._icon.update_menu()
			time.sleep(1)

	def _create_default_icon(self, size=64, color1='blue', color2='white'):
		image = Image.new('RGB', (size, size), color1)
		draw = ImageDraw.Draw(image)
		draw.rectangle([size // 4, size // 4, 3 * size // 4, 3 * size // 4], fill=color2)
		return image

	def _open_browser(self):
		"""Open browser at localhost"""
		url = f'http://localhost:{settings.PORT}'
		webbrowser.open(url)

	def _build_restart_command(self) -> list[str]:
		if getattr(sys, 'frozen', False):
			return [sys.executable, *sys.argv[1:]]

		return [sys.executable, *sys.argv]

	def restart_application(self):
		env = os.environ.copy()

		if getattr(sys, 'frozen', False):
			# Force a fresh onefile extraction for the restarted process.
			env['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
			env.pop('_MEIPASS2', None)

		subprocess.Popen(self._build_restart_command(), env=env, cwd=os.getcwd())
		self.exit_application()

	def exit_application(self):
		if self._icon:
			self._icon.stop()
		os._exit(0)
