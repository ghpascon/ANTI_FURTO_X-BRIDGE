import logging
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse, RedirectResponse


def setup_exeptions(app):
	@app.exception_handler(404)
	async def not_found_handler(request: Request, exc: Any) -> RedirectResponse:
		"""Handle 404 Not Found errors by redirecting to the home page."""
		logging.warning(f'404 Not Found: {request.url}')
		return RedirectResponse(url=request.app.url_path_for('index'))

	@app.exception_handler(RequestValidationError)
	async def validation_exception_handler(
		request: Request, exc: RequestValidationError
	) -> JSONResponse:
		"""
		Handle request validation errors with detailed logging and response.

		Args:
		    request: The incoming request that failed validation
		    exc: The validation exception with error details

		Returns:
		    JSONResponse with validation error details
		"""
		# Get the request body for logging
		try:
			body = await request.body()
			body_text = body.decode('utf-8', errors='ignore')
		except Exception:
			body_text = '<unable to read body>'

		# Clean error details for safe JSON serialization
		errors = []
		for error in exc.errors():
			error_dict = {
				'loc': error.get('loc', []),
				'msg': str(error.get('msg', '')),
				'type': error.get('type', ''),
			}
			if 'input' in error:
				error_dict['input'] = str(error['input'])
			errors.append(error_dict)

		# Log validation error with details
		logging.error(
			f'Request validation error: {request.method} {request.url}\n'
			f'Headers: {dict(request.headers)}\n'
			f'Body: {body_text}\n'
			f'Errors: {errors}'
		)

		# Return structured error response
		return JSONResponse(
			status_code=422,
			content={
				'detail': errors,
				'body': body_text,
				'message': 'Invalid request received',
			},
		)
