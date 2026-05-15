import logging

try:
	from ._main import TrayManager
	from app.core import settings
	from app.core import ICON_PATH

	tray_manager = TrayManager(app_name=settings.TITLE, icon_path=ICON_PATH)
except Exception as e:
	logging.warning(f'TrayManager não pôde ser iniciado: {e}\nO sistema continuará sem tray.')

	import os
	import sys
	import subprocess

	class DummyTrayManager:
		def _build_restart_command(self):
			if getattr(sys, 'frozen', False):
				return [sys.executable, *sys.argv[1:]]
			return [sys.executable, *sys.argv]

		def restart_application(self, *args, **kwargs):
			logging.info('Reiniciando aplicação (dummy, sem tray)')
			env = os.environ.copy()
			if getattr(sys, 'frozen', False):
				env['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
				env.pop('_MEIPASS2', None)
			subprocess.Popen(self._build_restart_command(), env=env, cwd=os.getcwd())
			self.exit_application()

		def exit_application(self, *args, **kwargs):
			logging.info('Encerrando aplicação (dummy, sem tray)')
			os._exit(0)

	tray_manager = DummyTrayManager()
