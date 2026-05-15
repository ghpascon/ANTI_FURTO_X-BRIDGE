import tomli
from app import __version__
from app.core import DOCS_PATH
from pathlib import Path
import os


def get_toml_version():
	toml_path = Path(__file__).parent.parent / 'pyproject.toml'
	with open(toml_path, 'rb') as f:
		data = tomli.load(f)
		return data['tool']['poetry']['version']
	raise RuntimeError('Version not found in pyproject.toml')


def test_version_matches_toml():
	print(f'DOCS_PATH: {DOCS_PATH}')
	toml_version = get_toml_version()
	assert (
		__version__ == toml_version
	), f'App version {__version__} != pyproject.toml version {toml_version}'
	# Diagnóstico: verifica se o arquivo foi criado e mostra o caminho
	version_file = Path(DOCS_PATH) / 'version.txt'
	print(f'Esperado version_file: {version_file}')
	print(f'Existe? {version_file.exists()}')
	if version_file.exists():
		content = version_file.read_text(encoding='utf-8').strip()
		print(f'Conteúdo do version.txt: {content}')
		assert (
			content == toml_version
		), f'{version_file} version does not match pyproject.toml version'
	else:
		# Mostra arquivos do diretório para diagnóstico
		print(
			f"Arquivos em {DOCS_PATH}: {os.listdir(DOCS_PATH) if os.path.exists(DOCS_PATH) else 'Diretório não existe'}"
		)
		assert False, f'{version_file} não foi criado'
