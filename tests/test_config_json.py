import json
import os


def test_config_json_loads():
	config_path = os.path.join(os.path.dirname(__file__), '../config/config.json')
	assert os.path.exists(config_path), 'config.json não encontrado'
	with open(config_path, encoding='utf-8') as f:
		data = json.load(f)
	assert isinstance(data, dict)
	assert (
		'database_url' in data or 'DATABASE_URL' in data or 'db_url' in data
	), 'Config não possui campo de banco de dados principal'
