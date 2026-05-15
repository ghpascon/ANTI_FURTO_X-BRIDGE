from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import asyncio
import logging
import os

from smartx_rfid.utils.path import get_frozen_path, load_file, include_all_routers
from app.async_func import create_async_tasks
from .exeption_handlers import setup_exeptions
from .middleware import setup_middlewares


# Lifecicle
@asynccontextmanager
async def lifespan(app: FastAPI):
	"""
	Manage the asynchronous lifecycle of the application.

	This context manager handles startup and shutdown processes:
	- On startup: Creates and starts background tasks
	- On shutdown: Cancels all running background tasks

	Args:
	    app: The FastAPI application instance
	"""
	tasks: List[asyncio.Task] = []

	try:
		# Initialize background tasks
		tasks = await create_async_tasks(get_frozen_path('app/async_func'))
		logging.info(f'Started {len(tasks)} background tasks')
		yield
	except Exception as e:
		logging.error(f'Critical error during application lifecycle: {e}', exc_info=True)
	finally:
		# Ensure all background tasks are properly cancelled at shutdown
		logging.info('Shutting down application, cancelling background tasks')
		for task in tasks:
			if not task.done():
				task.cancel()

		if tasks:
			# Wait for all tasks to finish cancellation
			await asyncio.gather(*tasks, return_exceptions=True)
		logging.info('Application shutdown complete')


def create_application(title: str, swagger_path: str) -> FastAPI:
	"""
	Create and configure the FastAPI application.
	"""
	# Load API documentation
	markdown_description = load_file(swagger_path)

	# Create FastAPI instance
	app = FastAPI(
		lifespan=lifespan,
		title=title,
		description=markdown_description,
		redoc_url=None,
		docs_url=None,
	)

	# Configure exception handlers and middlewares
	setup_exeptions(app)
	setup_middlewares(app)

	# Mount static files directory
	static_dir = get_frozen_path('app/static')
	if os.path.exists(static_dir):
		app.mount('/static', StaticFiles(directory=static_dir), name='static')
	else:
		logging.warning(f'Static files directory not found: {static_dir}')

	# Include all routers from routers directory
	include_all_routers('app/routers', app)
	logging.info('Application successfully configured')

	return app
