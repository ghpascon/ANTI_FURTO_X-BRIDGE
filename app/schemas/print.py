from pydantic import BaseModel, Field
from smartx_rfid.devices.printer import simple_zpl_example


class PrintModel(BaseModel):
	zpl: str = Field(simple_zpl_example, description='ZPL code to be sent to the printer')
