from collections import deque
import hashlib

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

from app.core import templates
from app.core import logger

router = APIRouter(prefix='', tags=['Logs'])

_NO_LIMIT = object()


def _read_tail(file_path: str, n: Optional[int]) -> list[str]:
	"""Read the last *n* non-empty lines of a file efficiently using a deque.
	If *n* is None, all lines are returned."""
	with open(file_path, 'rb') as f:
		raw_lines = list(deque(f, n) if n is not None else f.readlines())
	return [line.decode('utf-8', errors='replace').strip() for line in raw_lines if line.strip()]


async def get_log_content(limit: Optional[int] = 500) -> Dict[str, Any]:
	"""
	Function to fetch log content and file information.

	Args:
		limit: Maximum number of lines to return (None = all lines).

	Returns:
		Dict containing log content, file metadata and content hash.
	"""
	file_path = logger._get_filename_for_date(datetime.now().date())

	total_lines = 0
	try:
		log_content = _read_tail(file_path, limit)
		# Count total lines for display purposes (cheap: count newlines)
		if os.path.exists(file_path):
			with open(file_path, 'rb') as f:
				total_lines = sum(1 for line in f if line.strip())
	except FileNotFoundError:
		log_content = [
			json.dumps(
				{
					'level': 'ERROR',
					'message': 'Log file not found.',
					'timestamp': datetime.now().isoformat(),
				}
			)
		]
	except Exception as e:
		log_content = [
			json.dumps(
				{
					'level': 'ERROR',
					'message': f'Error reading log file: {str(e)}',
					'timestamp': datetime.now().isoformat(),
				}
			)
		]

	content_hash = hashlib.md5(''.join(log_content).encode()).hexdigest()  # noqa: S324

	log_info = {
		'file_path': file_path,
		'file_exists': os.path.exists(file_path),
		'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
		'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime(
			'%Y-%m-%d %H:%M:%S'
		)
		if os.path.exists(file_path)
		else 'N/A',
		'total_lines': total_lines,
		'returned_lines': len(log_content),
		'timestamp': datetime.now().isoformat(),
	}

	return {'content': log_content, 'info': log_info, 'hash': content_hash}


@router.get('/logs', response_class=HTMLResponse)
async def logs(request: Request):
	return templates.TemplateResponse(
		'pages/logs/main.html',
		{
			'request': request,
			'title': 'Logs',
			'alerts': [],
		},
		media_type='text/html; charset=utf-8',
	)


@router.get('/logs/get_content')
async def get_logs_content(limit: Optional[int] = 500, last_hash: Optional[str] = None):
	"""Return log lines.

	Query params:
	- limit: number of lines to return from the end of the file (omit or 0 = all).
	- last_hash: MD5 of the last received content. If unchanged, returns 304-style empty response.
	"""
	effective_limit = limit if limit and limit > 0 else None
	log_data = await get_log_content(limit=effective_limit)

	if last_hash and log_data['hash'] == last_hash:
		return JSONResponse(
			content={'changed': False, 'hash': log_data['hash']},
			headers={'Cache-Control': 'no-cache, no-store, must-revalidate'},
		)

	return JSONResponse(
		content={**log_data, 'changed': True},
		headers={'Cache-Control': 'no-cache, no-store, must-revalidate'},
	)
