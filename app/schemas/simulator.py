import re

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class TagListSimulator(BaseModel):
	start_epc: str = Field('000000000000000000000001')
	qtd: int = 50

	@field_validator('start_epc')
	def validate_epc_length_and_hex(cls, v, info: ValidationInfo):
		if len(v) != 24:
			raise ValueError(f'{info.field_name} must have exactly 24 characters')
		if not re.fullmatch(r'[0-9a-fA-F]{24}', v):
			raise ValueError(
				f'{info.field_name} must contain only hexadecimal characters (0-9, a-f)'
			)
		return v.lower()


class TagGtinSimulator(BaseModel):
	gtin: str = Field('07894900011517')
	qtd: int = 50
	start_serial: int = Field(1)

	@field_validator('gtin')
	def validate_gtin(cls, v):
		if not re.fullmatch(r'\d{14}', v):
			raise ValueError('GTIN must have exactly 14 digits')
		return v

	@field_validator('qtd')
	def validate_qtd(cls, v):
		if v <= 0 or v > 10000:
			raise ValueError('qtd must be between 1 and 10000')
		return v

	@field_validator('start_serial')
	def validate_start_serial(cls, v):
		if v < 1:
			raise ValueError('start_serial must be at least 1')
		return v


class CustomTagSimulator(BaseModel):
	epc: str = Field('000000000000000000000001')
	tid: str = Field('e28000000000000000000001')
	ant: int = Field(1)
	rssi: int = Field(-50)

	@field_validator('epc')
	def validate_epc_length_and_hex(cls, v, info: ValidationInfo):
		if len(v) % 4 != 0:
			raise ValueError(f'{info.field_name} length must be a multiple of 4 characters')
		if not re.fullmatch(r'[0-9a-fA-F]+', v):
			raise ValueError(
				f'{info.field_name} must contain only hexadecimal characters (0-9, a-f)'
			)
		return v.lower()

	@field_validator('tid')
	def validate_tid_length_and_hex(cls, v, info: ValidationInfo):
		if len(v) != 24:
			raise ValueError(f'{info.field_name} must have exactly 24 characters')
		if not re.fullmatch(r'[0-9a-fA-F]{24}', v):
			raise ValueError(
				f'{info.field_name} must contain only hexadecimal characters (0-9, a-f)'
			)
		return v.lower()

	@field_validator('rssi')
	def validate_rssi(cls, v):
		if v > 0:
			raise ValueError('rssi must be a negative value')
		return v
