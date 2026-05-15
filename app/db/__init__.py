from smartx_rfid.db import DatabaseManager
import logging
from app.models import get_all_models


def setup_database(database_url: str = None) -> DatabaseManager:
	logging.info('Initializing DatabaseManager')
	db_manager = DatabaseManager(database_url=database_url, echo=True, pool_size=5, pool_timeout=30)

	logging.info('Initializing database...')
	db_manager.initialize()

	logging.info('Registering models...')
	models = get_all_models()
	for model in models:
		logging.info(f'Registering model: {model.__name__}')
		db_manager.register_models(model)

	logging.info('Creating tables...')
	db_manager.create_tables()

	logging.info('DatabaseManager setup complete.')

	return db_manager
