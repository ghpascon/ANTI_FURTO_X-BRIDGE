from app.db import setup_database
from smartx_rfid.db import DatabaseManager
from smartx_rfid.webhook import WebhookManager, WebhookXtrack
import logging
from app.models.rfid import Tag, Event
from app.core import settings
import asyncio
from app.core import Indicator
from typing import Any

from app.models import Base
from app.services.license import license_manager


class Integration:
	def __init__(self):
		self.db_manager: DatabaseManager | None = None
		self.webhook_manager: WebhookManager | None = None
		self.webhook_xtrack: WebhookXtrack | None = None
		self.indicator: Indicator | None = Indicator() if settings.BEEP else None
		self.setup_integration()

	async def _run_integration_tasks(self, context: str, tasks: list):
		"""Run integration tasks without letting one failure abort the others."""
		if not tasks or not license_manager.validate_license():
			return

		logging.info(f'[{context}] Executing {len(tasks)} tasks concurrently')
		results = await asyncio.gather(*tasks, return_exceptions=True)
		for result in results:
			if isinstance(result, Exception):
				logging.error(
					f'[{context}] Task failed: {result}',
					exc_info=(type(result), result, result.__traceback__),
				)

	# [ SETUP ]
	def setup_integration(self):
		self.load_database()
		self.load_webhook()
		self.load_webhook_xtrack()

	def load_database(self):
		self.db_manager = None
		try:
			if settings.DATABASE_URL is not None:
				logging.info('Setting up Database Integration')
				self.db_manager: DatabaseManager = setup_database(
					database_url=settings.DATABASE_URL
				)
				return True
			else:
				logging.warning('DATABASE_URL not set. Skipping Database Integration setup.')
				return False
		except Exception as e:
			logging.error(f'Error setting up Database Integration: {e}')
			return False

	def load_webhook(self):
		self.webhook_manager = None
		try:
			if settings.WEBHOOK_URL is not None:
				logging.info('Setting up Webhook Integration')
				self.webhook_manager = WebhookManager(
					url=settings.WEBHOOK_URL, timeout=1, max_retries=1
				)
				return True
			else:
				logging.warning('WEBHOOK_URL not set. Skipping Webhook Integration setup.')
				return False
		except Exception as e:
			logging.error(f'Error setting up Webhook Integration: {e}')
			return False

	def load_webhook_xtrack(self):
		self.webhook_xtrack = None
		try:
			if settings.XTRACK_URL is not None:
				logging.info('Setting up Webhook Xtrack Integration')
				self.webhook_xtrack = WebhookXtrack(url=settings.XTRACK_URL, timeout=1)
				return True
			else:
				logging.warning('XTRACK_URL not set. Skipping Webhook Xtrack Integration setup.')
				return False
		except Exception as e:
			logging.error(f'Error setting up Webhook Xtrack Integration: {e}')
			return False

	# [ EVENT ]
	async def on_event_integration(self, name: str, event_type: str, event_data: Any):
		"""
		Handle integration of events into the database.

		Args:
		    name: Name of the device
		    event_type: Type of event
		    event_data: Data of the event
		"""
		tasks = []

		# DATABASE INTEGRATION
		if self.db_manager is not None:
			logging.info('[ EVENT INTEGRATION ] DATABASE')
			tasks.append(
				asyncio.to_thread(
					self._event_database_integration,
					name=name,
					event_type=event_type,
					event_data=event_data,
				)
			)

		# WEBHOOK INTEGRATION
		if self.webhook_manager is not None:
			logging.info('[ EVENT INTEGRATION ] WEBHOOK')
			tasks.append(
				self.webhook_manager.post_event(
					device=name, event_type=event_type, event_data=event_data
				)
			)

		await self._run_integration_tasks('EVENT INTEGRATION', tasks)

	def _event_database_integration(self, name: str, event_type: str, event_data: dict):
		"""Save event to database."""
		with self.db_manager.get_session() as session:
			session.add(
				Event(
					device=name,
					event_type=event_type,
					event_data=str(event_data),  # Convert dict to string for Text field
				)
			)
			session.commit()

	# [ TAG ]
	async def on_tag_integration(self, tag: dict):
		"""
		Handle integration of tag reads into the database.

		Args:
		    device: Device name
		    tag_data: Data of the read tag
		"""
		tasks = []

		# DATABASE INTEGRATION
		if self.db_manager is not None:
			logging.info('[ TAG INTEGRATION ] DATABASE')
			tasks.append(asyncio.to_thread(self._tag_database_integration, data=tag))

		# WEBHOOK INTEGRATION
		if self.webhook_manager is not None:
			logging.info('[ TAG INTEGRATION ] WEBHOOK')
			tasks.append(
				self.webhook_manager.post_event(
					device=tag.get('device'), event_type='tag', event_data=tag
				)
			)

		# XTRACK INTEGRATION
		if self.webhook_xtrack is not None:
			logging.info('[ TAG INTEGRATION ] XTRACK')
			tasks.append(self.webhook_xtrack.post(tag))

		# Beep
		if settings.BEEP and self.indicator is not None:
			logging.info('[ TAG INTEGRATION ] BEEP')
			tasks.append(self.indicator.beep())

		await self._run_integration_tasks('TAG INTEGRATION', tasks)

	def _tag_database_integration(self, data: dict):
		"""Save tag to database."""
		with self.db_manager.get_session() as session:
			session.add(Tag.from_dict(data))
			session.commit()

	def generate_table_report(self, model: Base, limit: int = 1000, offset: int = 0) -> dict:
		"""
		Generate table report with pagination for better performance.

		Args:
		    model: SQLAlchemy model to query
		    limit: Maximum number of records to return (default: 1000)
		    offset: Number of records to skip (default: 0)

		Returns:
		    dict with 'data', 'total', 'limit', and 'offset' keys
		"""
		if self.db_manager is None:
			raise Exception('Database manager is not initialized')

		with self.db_manager.get_session() as session:
			# Get total count (more efficient than loading all records)
			total = session.query(model).count()

			# Get paginated records using yield_per for memory efficiency
			if limit is None or limit <= 0:
				limit = total  # If no limit, return all records
				offset = 0  # Reset offset if returning all records
			query = session.query(model).limit(limit).offset(offset)
			records = [record.to_dict() for record in query]

			return {
				'total': total,
				'limit': limit,
				'offset': offset,
				'has_more': (offset + limit) < total,
				'data': records,
			}
