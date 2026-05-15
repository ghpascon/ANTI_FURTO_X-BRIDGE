import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from smartx_rfid.utils.path import get_prefix_from_path
from app.schemas.protected import ProtectedInventoryModel, ProtectedModeModel, ProtectListModel
from smartx_rfid.schemas.devices import GpoSchema

from app.services import rfid_manager
from app.schemas.print import PrintModel

router_prefix = get_prefix_from_path(__file__)
router = APIRouter(prefix=router_prefix, tags=[router_prefix])


@router.get(
	'/get_devices',
	summary='Get registered devices',
	description='Returns a list of all registered RFID devices.',
)
async def get_devices():
	return rfid_manager.devices.get_devices()


@router.get(
	'/get_device_config/{device_name}',
	summary='Get device configuration',
	description='Returns the current configuration of the specified device.',
)
async def get_device_config(device_name: str):
	config = rfid_manager.devices.get_device_config(name=device_name)
	if config is None:
		return JSONResponse(
			status_code=404,
			content={'message': f"Device '{device_name}' not found."},
		)
	return JSONResponse(status_code=200, content=config)


@router.get(
	'/get_device_types_list',
	summary='Get list of supported device types',
	description='Returns a list of supported device types that can be configured.',
)
async def get_device_types_list():
	return rfid_manager.devices.get_device_types_example()


@router.get(
	'/get_device_config_example/{device_name}',
	summary='Get example device configuration',
	description='Returns an example configuration for the specified device type.',
)
async def get_device_config_example(device_name: str):
	config = rfid_manager.devices.get_device_config_example(name=device_name)
	if config is None:
		return JSONResponse(
			status_code=404,
			content={'message': f"Example configuration for device '{device_name}' not found."},
		)
	return JSONResponse(status_code=200, content=config)


@router.get(
	'/get_device_count',
	summary='Get device count',
	description='Returns the total number of registered RFID devices.',
)
async def get_device_count():
	return {'device_count': rfid_manager.devices.get_device_count()}


@router.get(
	'/get_device_info/{device_name}',
	summary='Get device information',
	description='Returns connection and reading status for the specified device.',
)
async def get_device_info(device_name: str):
	info = rfid_manager.devices.get_device_info(name=device_name)
	if len(info) == 0:
		return JSONResponse(
			status_code=404,
			content={'message': f"Device '{device_name}' not found."},
		)
	return JSONResponse(status_code=200, content=info[0])


@router.get(
	'/get_devices_info',
	summary='Get all devices information',
	description='Returns connection and reading status for all registered devices.',
)
async def get_devices_info():
	info = rfid_manager.devices.get_device_info()
	return JSONResponse(status_code=200, content=info)


@router.get(
	'/any_device_reading',
	summary='Check if any device is reading',
	description='Returns true if any registered device is currently reading tags.',
)
async def any_device_reading():
	is_reading = rfid_manager.devices.any_device_reading()
	return {'any_device_reading': is_reading}


@router.post(
	'/start_inventory/{device_name}',
	summary='Start device inventory',
	description='Starts the inventory process for the specified device.',
)
async def start_device_inventory(device_name: str):
	success = await rfid_manager.devices.start_inventory(name=device_name)
	if not success:
		return JSONResponse(
			status_code=404,
			content={'message': f"Device '{device_name}' not found or could not start inventory."},
		)
	return {'message': f"Inventory started for device '{device_name}'."}


@router.post(
	'/stop_inventory/{device_name}',
	summary='Stop device inventory',
	description='Stops the inventory process for the specified device.',
)
async def stop_device_inventory(device_name: str):
	success = await rfid_manager.devices.stop_inventory(name=device_name)
	if not success:
		return JSONResponse(
			status_code=404,
			content={'message': f"Device '{device_name}' not found or could not stop inventory."},
		)
	return {'message': f"Inventory stopped for device '{device_name}'."}


@router.post(
	'/start_inventory_all',
	summary='Start inventory on all devices',
	description='Starts the inventory process for all connected RFID devices.',
)
async def start_inventory_all():
	results = await rfid_manager.devices.start_inventory_all()
	success_count = sum(1 for success in results.values() if success)
	total_count = len(results)
	return {
		'message': f'Inventory started on {success_count}/{total_count} devices.',
		'results': results,
	}


@router.post(
	'/stop_inventory_all',
	summary='Stop inventory on all devices',
	description='Stops the inventory process for all connected RFID devices.',
)
async def stop_inventory_all():
	results = await rfid_manager.devices.stop_inventory_all()
	success_count = sum(1 for success in results.values() if success)
	total_count = len(results)
	return {
		'message': f'Inventory stopped on {success_count}/{total_count} devices.',
		'results': results,
	}


@router.post(
	'/protected_inventory/{device_name}',
	summary='Start or stop protected inventory on a device',
	description='Starts or stops the protected inventory process on the specified device.',
)
async def protected_inventory(device_name: str, protected_inventory: ProtectedInventoryModel):
	print(protected_inventory.model_dump())
	success, msg = await rfid_manager.devices.protected_inventory(
		device_name, **protected_inventory.model_dump()
	)
	if success:
		return JSONResponse(
			status_code=200,
			content={
				'message': f"Command sent successfully to device '{device_name}'.",
			},
		)
	return JSONResponse(
		status_code=400,
		content={'message': f"Failed to send command to device '{device_name}'.", 'error': msg},
	)


@router.post(
	'/protected_mode/{device_name}',
	summary='Activate/deactivate protected mode on a tag',
	description='Activates or deactivates the protected mode on a tag for the specified device.',
)
async def protected_mode(device_name: str, protected_mode: ProtectedModeModel):
	success, msg = await rfid_manager.devices.protected_mode(
		device_name, **protected_mode.model_dump()
	)
	if success:
		return JSONResponse(
			status_code=200,
			content={
				'message': f"Command sent successfully to device '{device_name}'.",
			},
		)
	return JSONResponse(
		status_code=400,
		content={'message': f"Failed to send command to device '{device_name}'.", 'error': msg},
	)


@router.post(
	'/protected_list/{device_name}',
	summary='Start or stop protected inventory on a list of tags',
	description='Starts or stops the protected inventory process on a list of tags for the specified device.',
)
async def protected_list(device_name: str, protect_list: ProtectListModel):
	success_count = 0
	error_count = 0
	errors = []
	for epc in protect_list.epcs:
		success, msg = await rfid_manager.devices.protected_mode(
			device_name=device_name,
			epc=epc,
			password=protect_list.password,
			active=protect_list.active,
		)
		if success:
			success_count += 1
		else:
			error_count += 1
			errors.append({'epc': epc, 'error': msg})
	status_code = 200 if error_count == 0 else 207  # 207: Multi-Status
	return JSONResponse(
		status_code=status_code,
		content={
			'message': f"Commands sent to device '{device_name}'.",
			'success_count': success_count,
			'error_count': error_count,
			'errors': errors if error_count > 0 else None,
		},
	)


@router.post(
	'/print/{device_name}',
	summary='If device is a printer, send print command',
	description='Sends a print command to the specified printer device.',
)
async def print_to_device(device_name: str, content: PrintModel):
	logging.info(rfid_manager.devices.get_device_info(device_name))
	success, msg = rfid_manager.devices.print(device_name, data=content.zpl)
	if success:
		return JSONResponse(
			status_code=200,
			content={
				'message': f"Print command sent successfully to device '{device_name}'.",
			},
		)
	return JSONResponse(
		status_code=400,
		content={
			'message': f"Failed to send print command to device '{device_name}'.",
			'error': msg,
		},
	)


@router.post(
	'/add_to_print_queue/{device_name}',
	summary='Add print zpl or list of zpl to printer queue',
	description='Adds a print job to the print queue of the specified printer device.',
)
async def add_to_print_queue(device_name: str, content: PrintModel | list[PrintModel]):
	success = rfid_manager.devices.add_to_print_queue(
		device_name,
		zpl=content.zpl if isinstance(content, PrintModel) else [item.zpl for item in content],
	)
	if success:
		return JSONResponse(
			status_code=200,
			content={
				'message': f"Print job added to queue for device '{device_name}'.",
			},
		)
	return JSONResponse(
		status_code=400,
		content={
			'message': f"Failed to add print job to queue for device '{device_name}'.",
			'error': 'Device not found or not a printer.',
		},
	)


@router.post(
	'/write_gpo/{device_name}',
	summary='Write to GPO pin on a device',
	description='Writes a value to a specified GPO pin on the device.',
)
async def write_gpo(device_name: str, gpo_data: GpoSchema):
	success, msg = await rfid_manager.devices.write_gpo(
		device_name=device_name,
		**gpo_data.model_dump(),
	)
	if success:
		return JSONResponse(
			status_code=200,
			content={
				'message': f"GPO pin {gpo_data.pin} set to {gpo_data.state} on device '{device_name}'.",
			},
		)
	return JSONResponse(
		status_code=400,
		content={
			'message': f"Failed to write to GPO pin on device '{device_name}': {msg}",
			'error': msg,
		},
	)


@router.get(
	'/get_serial_number/{device_name}',
	summary='Get device serial number',
	description='Returns the serial number of the specified device.',
)
async def get_serial_number(device_name: str):
	success, serial_number = rfid_manager.devices.get_serial_number(device_name)
	if success:
		return JSONResponse(
			status_code=200,
			content={
				'device_name': device_name,
				'serial_number': serial_number,
			},
		)
	return JSONResponse(
		status_code=400,
		content={
			'message': f"Failed to get serial number for device '{device_name}': {serial_number}",
			'error': serial_number,
		},
	)
