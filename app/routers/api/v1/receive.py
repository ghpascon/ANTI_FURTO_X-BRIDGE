from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from smartx_rfid.utils.path import get_prefix_from_path
from smartx_rfid.schemas.tag import TagSchema
from smartx_rfid.schemas.events import EventSchema
from app.schemas.events import EventDeviceSchema
from app.services import rfid_manager

router_prefix = get_prefix_from_path(__file__)
router = APIRouter(prefix=router_prefix, tags=[router_prefix])


@router.post(
	'/tags/{device_name}',
	summary='Receive RFID tags',
	description='Endpoint to receive RFID tags from external sources.',
)
async def receive_tags(device_name: str, tags: list[TagSchema] | TagSchema):
	if isinstance(tags, TagSchema):
		tags = [tags]

	for tag in tags:
		rfid_manager.on_event(name=device_name, event_type='tag', event_data=tag.model_dump())

	return JSONResponse(
		status_code=200,
		content={'message': 'Tags received successfully.', 'received_count': len(tags)},
	)


@router.post(
	'/events/{device_name}',
	summary='Receive RFID events',
	description='Endpoint to receive RFID events from external sources.',
)
async def receive_events(device_name: str, events: list[EventSchema] | EventSchema):
	if isinstance(events, EventSchema):
		events = [events]

	for event in events:
		rfid_manager.on_event(
			name=device_name,
			event_type=event.event_type,
			event_data=event.event_data,
		)

	return JSONResponse(
		status_code=200,
		content={'message': 'Events received successfully.', 'received_count': len(events)},
	)


@router.post(
	'/x714',
	summary='Receive X714 events',
	description='Endpoint to receive non-standardized JSON events from X714 devices.',
)
async def receive_x714(events: list[EventDeviceSchema] | EventDeviceSchema):
	if isinstance(events, EventDeviceSchema):
		events = [events]

	for event in events:
		rfid_manager.on_event(
			name=event.device_name,
			event_type=event.event_type,
			event_data=event.event_data,
		)

	return JSONResponse(
		status_code=200,
		content={'message': 'X714 events received successfully.', 'received_count': len(events)},
	)


@router.post(
	'/r700',
	summary='Receive R700 events',
	description='Endpoint to receive non-standardized JSON events from R700 devices.',
)
async def receive_r700(request: Request):
	data = await request.json()

	if isinstance(data, list):
		events = data
	else:
		events = [data]

	rfid_manager.handle_r700_event(events)
	return JSONResponse(
		status_code=200,
		content={'message': f'{len(events)} events received'},
	)


@router.post(
	'/x-scan',
	summary='Receive X-SCAN events',
	description='Endpoint to receive non-standardized JSON events from X-SCAN devices.',
)
async def receive_x_scan(events: list[EventDeviceSchema] | EventDeviceSchema):
	if isinstance(events, EventDeviceSchema):
		events = [events]

	for event in events:
		rfid_manager.on_xscan_event(**event.model_dump())

	return JSONResponse(
		status_code=200,
		content={'message': 'X-SCAN events received successfully.', 'received_count': len(events)},
	)
