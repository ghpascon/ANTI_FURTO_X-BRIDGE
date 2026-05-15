import os
from smartx_rfid.utils.path import get_frozen_path
import logging
import warnings

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
warnings.filterwarnings('ignore', category=UserWarning, module='pygame.pkgdata')

import pygame  # noqa: E402


class Indicator:
	def __init__(self):
		# Initialize pygame mixer
		try:
			pygame.mixer.init()
		except Exception as e:
			logging.error(f'Erro inicializando mixer do pygame: {e}')

		# load sounds
		# Carregar sons
		self.beep_sound = self.load_sound('beep.wav')

	def load_sound(self, filename: str):
		sound_path = get_frozen_path(f'app/static/sounds/{filename}')
		if os.path.exists(sound_path):
			try:
				return pygame.mixer.Sound(sound_path)
			except Exception as e:
				logging.error(f'Erro carregando {filename}: {e}')
				return None
		else:
			logging.error(f'Arquivo de som não encontrado: {sound_path}')
			return None

	async def beep(self):
		"""
		Executa o som de beep.
		"""
		if self.beep_sound is not None:
			try:
				self.beep_sound.play()
			except Exception:
				pass
