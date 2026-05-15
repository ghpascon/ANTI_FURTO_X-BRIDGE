from fastapi import APIRouter, Path
from fastapi.responses import JSONResponse
from smartx_rfid.utils.path import get_prefix_from_path
from smartx_rfid.schemas.tag import WriteTagValidator
from app.schemas import write_tag_example

from app.services import rfid_manager

router_prefix = get_prefix_from_path(__file__)
router = APIRouter(prefix=router_prefix, tags=[router_prefix])


@router.get(
	'/get_tags',
	summary='Get all tags',
	description='Returns a list of all detected RFID tags.',
)
async def get_tags():
	return rfid_manager.tags.get_all()


@router.get(
	'/get_n_tags/{limit}',
	summary='Get limited tags',
	description='Returns only the first N detected RFID tags.',
)
async def get_n_tags(limit: int = Path(..., ge=0)):
	return rfid_manager.tags.get_all(limit=limit)


@router.get(
	'/get_tag_count',
	summary='Get tag count',
	description='Returns the total number of detected RFID tags.',
)
async def get_tag_count():
	return {'count': len(rfid_manager.tags)}


@router.post(
	'/clear_tags',
	summary='Clear all tags',
	description='Removes all detected RFID tags from the system.',
)
async def clear_tags():
	rfid_manager.tags.clear()
	return JSONResponse(
		status_code=200,
		content={'message': 'All tags have been cleared.'},
	)


@router.post(
	'/clear_tags_device/{device_name}',
	summary='Clear all tags for a specific device',
	description='Removes all detected RFID tags from the system for a specified device.',
)
async def clear_tags_device(device_name: str):
	rfid_manager.tags.remove_tags_by_device(device=device_name)
	return JSONResponse(
		status_code=200,
		content={'message': f'All tags for device {device_name} have been cleared.'},
	)


@router.get(
	'/get_epcs',
	summary='Get all EPCs',
	description='Returns a list of all detected EPCs from RFID tags.',
)
async def get_epcs():
	return rfid_manager.tags.get_epcs()


@router.get(
	'/get_n_epcs/{limit}',
	summary='Get limited EPCs',
	description='Returns only the first N detected EPCs from RFID tags.',
)
async def get_n_epcs(limit: int = Path(..., ge=0)):
	return rfid_manager.tags.get_epcs(limit=limit)


@router.get(
	'/get_tids',
	summary='Get all TIDs',
	description='Returns a list of all detected TIDs from RFID tags.',
)
async def get_tids():
	tags = rfid_manager.tags.get_all()
	return [tag.get('tid') for tag in tags]


@router.get(
	'/get_gtin_count',
	summary='Get GTIN count',
	description='Returns the total number of unique GTINs from detected RFID tags.',
)
async def get_gtin_count():
	return rfid_manager.tags.get_gtin_counts()


@router.get(
	'/get_tag_info/{epc}',
	summary='Get tag information',
	description='Returns detailed information about detected RFID tags.',
)
async def get_tag_info(epc: str):
	return rfid_manager.tags.get_by_identifier(identifier_value=epc, identifier_type='epc')


@router.post(
	'/write_epc/{device_name}',
	summary='Write EPC to a tag',
	description='Writes an EPC to a specified RFID tag.',
	openapi_extra=write_tag_example,
)
async def write_epc(device_name: str, write_tag: WriteTagValidator):
	status, msg = await rfid_manager.devices.write_epc(device_name, write_tag)
	if not status:
		return JSONResponse(status_code=400, content={'message': msg})
	return JSONResponse(status_code=200, content={'message': 'Write epc command sent successfully'})
