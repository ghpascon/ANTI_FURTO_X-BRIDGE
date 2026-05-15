import asyncio
from app import __version__

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from smartx_rfid.utils.path import get_prefix_from_path

from app.services.settings_service import settings_service
from app.schemas.application import SettingsSchema
from app.core import settings
from smartx_rfid.utils import delayed_function
from app.services.tray import tray_manager
from app.core import alerts_manager

from app.services import rfid_manager
from app.models import get_all_models

router_prefix = get_prefix_from_path(__file__)
router = APIRouter(prefix=router_prefix, tags=[router_prefix])


@router.post('/restart_application_route')
async def restart_application_route():
	asyncio.create_task(delayed_function(tray_manager.restart_application, 1))
	return JSONResponse(content={'status': 'restarting'})


@router.post('/exit_application_route')
async def exit_application_route():
	asyncio.create_task(delayed_function(tray_manager.exit_application, 1))
	return JSONResponse(content={'status': 'exiting'})


@router.get('/get_current_settings', summary='Get the current application settings')
async def get_current_settings():
	return JSONResponse(content=settings.get_current_settings())


@router.post(
	'/update_settings',
	summary='Update the current application settings',
	description='Update the current application settings with the provided data',
)
async def update_settings(settings_data: SettingsSchema):  # type: ignore
	settings_service.update_settings(settings_data.model_dump(exclude_unset=True))
	return JSONResponse(content={'status': 'updated', 'settings': settings.get_current_settings()})


@router.post('/create_device/{device_name}', summary='Create a new device configuration')
async def create_device(device_name: str, data: dict):
	success, error = settings_service.create_device(device_name, data)
	if success:
		return JSONResponse(content={'status': 'created', 'device': device_name})
	return JSONResponse(content={'status': 'error', 'message': error}, status_code=400)


@router.put('/update_device/{device_name}', summary='Update an existing device configuration')
async def update_device(device_name: str, data: dict):
	success, error = settings_service.update_device(device_name, data)
	if success:
		return JSONResponse(content={'status': 'updated', 'device': device_name})
	return JSONResponse(content={'status': 'error', 'message': error}, status_code=400)


@router.delete('/delete_device/{device_name}', summary='Delete a device configuration')
async def delete_device(device_name: str):
	success, error = settings_service.delete_device(device_name)
	if success:
		return JSONResponse(content={'status': 'deleted', 'device': device_name})
	return JSONResponse(content={'status': 'error', 'message': error}, status_code=400)


@router.get('/has_changes', summary='Check if there are unsaved changes in the settings')
async def has_changes():
	return JSONResponse(content={'has_changes': settings_service.has_changes})


@router.get('/get_application_config_example', summary='Get the example configuration')
async def get_application_config_example():
	return JSONResponse(content=settings_service._get_example_config())


@router.get('/backup_config', summary='Backup the application configuration')
async def backup_config():
	return JSONResponse(content=settings_service.backup_config())


@router.post('/import_config', summary='Import the application configuration')
async def import_config(data: dict):
	return JSONResponse(content=settings_service.import_config(data))


@router.get('/get_version', summary='Get the current application version')
async def get_version():
	return JSONResponse(content={'version': __version__})


@router.get('/get_alerts', summary='Get current alerts')
async def get_alerts():
	return JSONResponse(content=alerts_manager.get_alerts())


@router.get(
	'/generate_table_report/{table_name}',
	summary='Generate table report',
	description='Generates a report for a specified database table.',
)
async def generate_table_report(table_name: str, limit: int = 1000, offset: int = 0):
	# Validate table
	models = get_all_models()
	valid_table = False
	table_model = None
	for model in models:
		if table_name == model.__tablename__:
			valid_table = True
			table_model = model
			break

	if not valid_table:
		return JSONResponse(status_code=400, content={'error': 'Invalid table name'})

	try:
		return rfid_manager.integration.generate_table_report(
			model=table_model, limit=limit, offset=offset
		)
	except Exception as e:
		return JSONResponse(status_code=500, content={'error': str(e)})
