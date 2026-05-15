from typing import Any
from pydantic import BaseModel, Field, create_model

from app.core import settings


def create_settings_schema() -> type[BaseModel]:
	data = settings.get_current_settings()

	type_mapping = {
		str: str,
		int: int,
		bool: bool,
		float: float,
		list: list,
		dict: dict,
	}

	fields = {}

	for key, value in data.items():
		if value is None:
			fields[key] = (Any, Field(default=None))
		else:
			value_type = type(value)
			field_type = type_mapping.get(value_type, Any)
			fields[key] = (field_type | None, Field(default=value))

	return create_model('SettingsSchema', **fields)


SettingsSchema: type[BaseModel] = create_settings_schema()
