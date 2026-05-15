import inspect
import logging
import sys
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from app.services.license import license_manager
from fastapi.responses import RedirectResponse

# =====================
#  AUTO-REGISTRATION
# =====================


def setup_middlewares(app: FastAPI):
	"""Automatically register all BaseHTTPMiddleware subclasses defined in this module"""

	# CORS middleware
	app.add_middleware(
		CORSMiddleware,
		allow_origins=['*'],
		allow_credentials=True,
		allow_methods=['GET', 'POST', 'PUT', 'DELETE'],
		allow_headers=['*'],
	)

	# Auto-register custom middlewares
	current_module = sys.modules[__name__]
	for name, obj in inspect.getmembers(current_module, inspect.isclass):
		if issubclass(obj, BaseHTTPMiddleware) and obj is not BaseHTTPMiddleware:
			app.add_middleware(obj)
			print(f'[Middleware] Registered: {name}')

	app.add_middleware(GZipMiddleware, minimum_size=1000)
	Instrumentator().instrument(app).expose(app, include_in_schema=False)


class SafeRequestMiddleware(BaseHTTPMiddleware):
	"""
	Middleware that wraps every request in a try/except block.
	Returns a JSON error response if any unhandled exception occurs.
	"""

	async def dispatch(self, request, call_next):
		try:
			response = await call_next(request)
			return response
		except Exception as e:
			# Log the error with traceback
			logging.error(f'[Middleware Error] {type(e).__name__}: {e}', exc_info=True)

			# Return JSON error response with safe serialization
			return JSONResponse(
				status_code=500,
				content={
					'message': str(e),
					'error_type': type(e).__name__,
					'path': request.url.path,
				},
			)


class LicenseValidationMiddleware(BaseHTTPMiddleware):
	"""
	Middleware that checks for a valid license before processing any request.
	If the license is invalid, it returns a 403 Forbidden response.
	"""

	async def dispatch(self, request, call_next):
		is_valid = license_manager.validate_license()
		path = request.url.path
		valid_path = path.startswith('/static') or '/license' in path
		if valid_path:
			return await call_next(request)
		if path.startswith('/api'):
			if not is_valid:
				return JSONResponse(
					status_code=403,
					content={'message': 'Invalid or missing license. Access denied.'},
				)
		else:
			if not is_valid:
				logging.warning(f'License validation failed for request to {request.url.path}')
				return RedirectResponse(url='/license')
		return await call_next(request)
