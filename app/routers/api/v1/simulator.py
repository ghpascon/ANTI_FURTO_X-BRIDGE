from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from smartx_rfid.utils.path import get_prefix_from_path
import logging

from app.services import rfid_manager

from app.schemas.simulator import TagListSimulator, TagGtinSimulator, CustomTagSimulator
from pyepc import SGTIN

router_prefix = get_prefix_from_path(__file__)
router = APIRouter(prefix=router_prefix, tags=[router_prefix])


@router.post(
	'/tag',
	summary='Simulate an RFID tag event',
	description='Simulates the reception of an RFID tag event for testing purposes.',
)
async def simulate_tag_event():
	sample_tag = {
		'epc': '000000000000000000000001',
		'tid': 'e28000000000000000000001',
		'ant': 1,
		'rssi': -50,
	}
	rfid_manager.on_event(
		name='SIMULATOR',
		event_type='tag',
		event_data=sample_tag,
	)
	return JSONResponse(
		status_code=200,
		content={'message': 'Simulated tag event successfully.'},
	)


@router.post(
	'/custom_tag',
	summary='Simulate a custom RFID tag event',
	description='Simulates the reception of a custom RFID tag event with user-defined data for testing purposes.',
)
async def simulate_custom_tag_event(custom_tag: CustomTagSimulator):
	tag_data = {
		'epc': custom_tag.epc,
		'tid': custom_tag.tid,
		'ant': custom_tag.ant,
		'rssi': custom_tag.rssi,
	}
	rfid_manager.on_event(
		name='SIMULATOR',
		event_type='tag',
		event_data=tag_data,
	)
	return JSONResponse(
		status_code=200,
		content={'message': 'Simulated custom tag event successfully.', 'tag_data': tag_data},
	)


@router.post(
	'/event',
	summary='Simulate a generic RFID event',
	description='Simulates the reception of a generic RFID event for testing purposes.',
)
async def simulate_generic_event():
	sample_event = {
		'event_type': 'custom_event',
		'event_data': {'info': 'This is a simulated event for testing.'},
	}
	rfid_manager.on_event(
		name='SIMULATOR',
		event_type=sample_event['event_type'],
		event_data=sample_event['event_data'],
	)
	return JSONResponse(
		status_code=200,
		content={'message': 'Simulated generic event successfully.'},
	)


@router.post(
	'/tag_list',
	summary='Simulate a list of RFID tag events',
	description='Simulates the reception of a list of RFID tag events for testing purposes.',
)
async def simulate_tag_list(tag_list: TagListSimulator):
	device_name = 'SIMULATOR'
	try:
		# Converte o EPC inicial para int para fazer incremento sequencial
		start_epc_int = int(tag_list.start_epc, 16)  # Adicionar base 16 para conversão hex

		tags_generated = []

		# Gera as tags sequencialmente
		for i in range(tag_list.qtd):
			# Calcula o EPC atual
			current_epc_int = start_epc_int + i
			current_epc = f'{current_epc_int:024x}'  # 24 caracteres hex com zero padding

			# Gera TID baseado no EPC (pode ser customizado)
			current_tid = f'e280{current_epc[4:]}'  # Prefixo comum + parte do EPC

			# Simula dados da tag
			tag_data = {
				'epc': current_epc,
				'tid': current_tid,
				'ant': (i % 4) + 1,  # Antenas de 1 a 4 alternadamente
				'rssi': -50 - (i % 30),  # RSSI variando entre -50 e -80
			}

			# Envia o evento para o sistema
			if not rfid_manager.on_tag(
				name=device_name,
				tag_data=tag_data,
			)[0]:
				continue
			tags_generated.append(tag_data)

		return JSONResponse(
			status_code=200,
			content={
				'message': f"Successfully simulated {tag_list.qtd} tag events from device '{device_name}'",
				'device': device_name,
				'tags_generated': len(tags_generated),
				'start_epc': tag_list.start_epc,
				'end_epc': tags_generated[-1]['epc'] if tags_generated else tag_list.start_epc,
			},
		)

	except ValueError as e:
		return JSONResponse(
			status_code=400,
			content={'error': f'Invalid EPC format: {str(e)}'},
		)
	except Exception as e:
		return JSONResponse(
			status_code=500,
			content={'error': f'Error generating tag list: {str(e)}'},
		)


@router.post(
	'/tag_gtin_list',
	summary='Simulate a list of RFID tag events based on GTIN',
	description='Simulates the reception of a list of RFID tag events based on GTIN for testing purposes.',
)
async def gtin_list(tag_generator: TagGtinSimulator):
	device_name = 'SIMULATOR'
	gtin = tag_generator.gtin
	qtd = tag_generator.qtd
	start_serial = tag_generator.start_serial

	# --- GTIN-14 Validation -------------------------------
	def validate_gtin14(gtin_str: str) -> bool:
		"""Validate GTIN-14 check digit using standard algorithm"""
		if len(gtin_str) != 14 or not gtin_str.isdigit():
			return False

		digits = [int(d) for d in gtin_str]
		check_digit = digits[-1]
		body = digits[:-1]

		# Weights 3 and 1 from right to left
		weights = [3 if (i % 2 == 0) else 1 for i in range(len(body) - 1, -1, -1)]

		total = sum(d * w for d, w in zip(body, weights))
		calc_digit = (10 - (total % 10)) % 10

		return calc_digit == check_digit

	# Validation check
	if not validate_gtin14(gtin):
		raise HTTPException(
			status_code=400,
			detail=f'GTIN {gtin} is invalid. Must contain 14 digits and pass check digit validation.',
		)

	# -------------------------------------------------------

	try:
		tags_generated = []

		# Generate sequential tags from GTIN
		for i in range(qtd):
			# Create SGTIN from GTIN and sequential serial number
			sgtin = SGTIN.from_sgtin(
				gtin=gtin,
				serial_number=str(start_serial + i),
				company_prefix_len=7,  # Standard 7-digit company prefix
			)
			# Encode to hexadecimal EPC
			epc_hex = sgtin.encode().lower()

			# Create tag data structure
			tag_data = {
				'epc': epc_hex,
				'tid': 'e280' + str(start_serial + i).zfill(20),  # TID can be None for SGTIN tags
				'ant': (i % 4) + 1,  # Rotate between antennas 1-4
				'rssi': -50 - (i % 30),  # RSSI varying between -50 and -80
			}

			# Send tag event to processing pipeline
			if not rfid_manager.on_tag(
				name=device_name,
				tag_data=tag_data,
			)[0]:
				continue

			tags_generated.append(tag_data)

		return JSONResponse(
			status_code=200,
			content={
				'message': f'Successfully generated {qtd} SGTIN tags from GTIN {gtin}',
				'device': device_name,
				'gtin': gtin,
				'tags_generated': len(tags_generated),
				'start_serial': start_serial,
				'end_serial': start_serial + qtd - 1,
			},
		)

	except Exception as e:
		logging.error(f'Error while processing GTIN tag generation: {e}')
		raise HTTPException(status_code=500, detail=f'Error generating GTIN tags: {str(e)}')
