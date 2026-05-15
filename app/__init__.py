from app.core import DOCS_PATH

import toml
import os


def _get_version():
	"""
	Try to get the version from pyproject.toml. If successful, save it to DOCS_PATH/version.txt.
	If not, try to read the version from DOCS_PATH/version.txt. If all fails, return 'unknown'.
	"""
	version = None
	pyproject_path = os.path.join(
		os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pyproject.toml'
	)
	version_file = os.path.join(DOCS_PATH, 'version.txt')
	try:
		with open(pyproject_path, 'r', encoding='utf-8') as f:
			pyproject_data = toml.load(f)
		version = pyproject_data.get('tool', {}).get('poetry', {}).get('version')
		if version:
			# Save version to version.txt
			os.makedirs(DOCS_PATH, exist_ok=True)
			with open(version_file, 'w', encoding='utf-8') as vf:
				vf.write(version)
			return version
	except Exception:
		pass
	# Try to read from version.txt
	try:
		with open(version_file, 'r', encoding='utf-8') as vf:
			version = vf.read().strip()
		if version:
			return version
	except Exception:
		pass
	return 'unknown'


__version__ = _get_version()
