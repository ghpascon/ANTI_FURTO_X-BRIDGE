import logging
import os
from typing import Any, Callable, Dict

from fastapi.templating import Jinja2Templates
from jinja2 import pass_context

from smartx_rfid.utils.path import get_frozen_path


@pass_context
def relative_url_for(context: Dict[str, Any], name: str, **path_params: Any) -> str:
	"""
	Build template URLs as relative paths (e.g. /auth/login).
	"""
	request = context.get('request')
	if request is None:
		raise ValueError("Template context missing 'request' for url_for")
	return request.url_for(name, **path_params).path


class TemplateManager:
	"""
	Manager for Jinja2 templates and global functions.
	"""

	def __init__(self, template_dir: str = 'app/templates'):
		"""
		Initialize TemplateManager and load templates.

		Args:
		    template_dir (str): Path to templates directory.
		"""
		self.template_dir = get_frozen_path(template_dir)
		self.templates: Jinja2Templates | None = None
		self._globals: Dict[str, Any] = {}
		self._initialize_templates()

	def _initialize_templates(self) -> None:
		"""
		Create Jinja2Templates instance and register default globals.

		Raises:
		    FileNotFoundError: If template directory doesn't exist
		    Exception: If template initialization fails
		"""
		if not os.path.exists(self.template_dir):
			error_msg = f'Template directory not found: {self.template_dir}'
			logging.error(error_msg)
			os.makedirs(
				self.template_dir, exist_ok=True
			)  # Create the directory to avoid future errors

		try:
			self.templates = Jinja2Templates(directory=self.template_dir)
			self.templates.env.globals['url_for'] = relative_url_for
			# Register default globals
			self._globals = self.get_default_globals()
			for name, func in self._globals.items():
				self.templates.env.globals[name] = func

			logging.info(f'Templates initialized successfully from: {self.template_dir}')
			logging.debug(
				f'Registered {len(self._globals)} template globals: {list(self._globals.keys())}'
			)

		except Exception as e:
			error_msg = f'Failed to initialize templates: {e}'
			logging.error(error_msg)
			raise Exception(error_msg)

	@staticmethod
	def get_default_globals() -> Dict[str, Any]:
		"""
		Get default template global functions and variables.

		Returns:
		    Dict[str, Any]: Dictionary of global template functions
		"""
		return {}

	def add_global(self, name: str, func: Callable) -> None:
		"""
		Add a new global function to the templates environment.

		Args:
		    name: Name of the global function
		    func: Function to add as global
		"""
		if self.templates and hasattr(self.templates, 'env'):
			self.templates.env.globals[name] = func
			logging.debug(f'Added template global: {name}')
		else:
			logging.warning(f"Cannot add template global '{name}': templates not initialized")
