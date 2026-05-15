from logging.config import fileConfig
import os
import sys
import json

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Load models and Base
from app.models import get_all_models
from smartx_rfid.models import Base

# Add project root to path to allow imports
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Load DATABASE_URL directly from config.json file
config_path = os.path.join(project_root, 'config', 'config.json')
database_url = None

if os.path.exists(config_path):
	try:
		with open(config_path, 'r', encoding='utf8') as f:
			config_data = json.load(f)
			database_url = config_data.get('DATABASE_URL')
	except Exception as e:
		print(f'Error loading config file: {e}')

if database_url is None:
	print('=' * 50)
	print('DATABASE_URL is not set in config/config.json')
	exit(1)


models = get_all_models()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
	fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
	"""Run migrations in 'offline' mode.

	This configures the context with just a URL
	and not an Engine, though an Engine is acceptable
	here as well.  By skipping the Engine creation
	we don't even need a DBAPI to be available.

	Calls to context.execute() here emit the given string to the
	script output.

	"""
	url = database_url or config.get_main_option('sqlalchemy.url')
	context.configure(
		url=url,
		target_metadata=target_metadata,
		literal_binds=True,
		dialect_opts={'paramstyle': 'named'},
	)

	with context.begin_transaction():
		context.run_migrations()


def run_migrations_online() -> None:
	"""Run migrations in 'online' mode.

	In this scenario we need to create an Engine
	and associate a connection with the context.

	"""
	# Use database_url from config.json if available
	config_section = config.get_section(config.config_ini_section, {})
	if database_url:
		config_section['sqlalchemy.url'] = database_url

	connectable = engine_from_config(
		config_section,
		prefix='sqlalchemy.',
		poolclass=pool.NullPool,
	)

	with connectable.connect() as connection:
		context.configure(connection=connection, target_metadata=target_metadata)

		with context.begin_transaction():
			context.run_migrations()


if context.is_offline_mode():
	run_migrations_offline()
else:
	run_migrations_online()
