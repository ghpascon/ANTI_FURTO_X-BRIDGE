from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core import templates

router = APIRouter(prefix='', tags=['Pages'])


@router.get('/settings/application', response_class=HTMLResponse)
async def settings_page(request: Request):
	return templates.TemplateResponse(
		'pages/application_settings/main.html',
		{'request': request, 'title': 'Settings', 'alerts': []},
		media_type='text/html; charset=utf-8',
	)


@router.get('/settings/devices', response_class=HTMLResponse)
async def devices_page(request: Request):
	return templates.TemplateResponse(
		'pages/devices_settings/main.html',
		{'request': request, 'title': 'Devices', 'alerts': []},
		media_type='text/html; charset=utf-8',
	)
