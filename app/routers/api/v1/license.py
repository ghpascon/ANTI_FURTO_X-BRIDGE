from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from smartx_rfid.utils.path import get_prefix_from_path
from app.services.license import license_manager
from app.core import LICENSE_PATH

router_prefix = get_prefix_from_path(__file__)
router = APIRouter(prefix=router_prefix, tags=[router_prefix])


@router.get('/get_license_info', summary='Get the current license information')
async def get_license_info():
	if license_manager is None:
		return JSONResponse(
			content={
				'valid': False,
				'license_info': None,
				'generate_key': None,
			},
			status_code=400,
		)

	valid = license_manager.validate_license()
	license_info = license_manager.license_data or {}

	if valid:
		return JSONResponse(
			content={
				'valid': True,
				'license_info': license_info,
				'generate_key': None,
			},
			status_code=200,
		)
	else:
		return JSONResponse(
			content={
				'valid': False,
				'license_info': {
					'expires': license_info.get('expires'),
				},
				'generate_key': license_manager.build_license_request_string(),
			},
			status_code=400,
		)


@router.post(
	'/upload_license',
	summary='Upload a new license string',
	description='Accepts a base64-encoded license string in the request body. Validates and loads it if correct.',
)
async def upload_license(license_string: str = Body(..., embed=True)):
	try:
		license_manager.load_license(license_string)
		# Save the new license string to file
		with open(LICENSE_PATH, 'w') as f:
			f.write(license_string)
		return JSONResponse(content={'message': 'License uploaded and valid'}, status_code=200)
	except Exception as e:
		return JSONResponse(content={'message': str(e)}, status_code=400)
