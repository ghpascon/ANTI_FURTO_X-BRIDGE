from pydantic import Field
from smartx_rfid.schemas.events import EventSchema


class EventDeviceSchema(EventSchema):
	device_name: str = Field(..., description='Name of the device associated with the event')
