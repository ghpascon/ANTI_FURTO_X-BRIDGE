from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core import templates

router = APIRouter(prefix='', tags=['Pages'])


@router.get('/protected_page', response_class=HTMLResponse)
async def protected_page(request: Request):
	return templates.TemplateResponse(
		'pages/protected_page/main.html',
		{'request': request, 'title': 'Protected', 'alerts': []},
		media_type='text/html; charset=utf-8',
	)


@router.get('/write_page', response_class=HTMLResponse)
async def write_page(request: Request):
	return templates.TemplateResponse(
		'pages/write_page/main.html',
		{'request': request, 'title': 'Write Tags', 'alerts': []},
		media_type='text/html; charset=utf-8',
	)


@router.get('/gpo_page', response_class=HTMLResponse)
async def gpo_page(request: Request):
	return templates.TemplateResponse(
		'pages/gpo_page/main.html',
		{'request': request, 'title': 'Gpo', 'alerts': []},
		media_type='text/html; charset=utf-8',
	)
