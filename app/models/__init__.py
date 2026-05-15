"""
Model auto-discovery module for SMARTX Connector.

This module automatically discovers and imports all SQLAlchemy models
from the models package, providing a centralized access point.
"""

import inspect
import pkgutil
from typing import List, Type

try:
	from sqlalchemy.orm import DeclarativeBase
except ImportError:
	from sqlalchemy.ext.declarative import declarative_base

	DeclarativeBase = declarative_base()

# Import all model modules to ensure they're registered
from smartx_rfid.models import Base, BaseMixin


def get_all_models() -> List[Type]:
	"""
	Automatically discover and return all SQLAlchemy models with DeclarativeBase.

	Returns:
	    List[Type]: List of all discovered model classes
	"""
	models = []

	# Get current module
	current_module = inspect.getmodule(inspect.currentframe())
	current_package = current_module.__package__ if current_module else None

	if not current_package:
		return models

	# Iterate through all modules in the package
	for _, name, _ in pkgutil.iter_modules(__path__, current_package + '.'):
		try:
			module = __import__(name, fromlist=[''])

			# Inspect all attributes in the module
			for attr_name in dir(module):
				attr = getattr(module, attr_name)

				# Check if it's a class and has SQLAlchemy table attributes
				if (
					inspect.isclass(attr)
					and hasattr(attr, '__tablename__')
					and hasattr(attr, '__table__')
					and attr.__module__ == name
				):
					models.append(attr)

		except (ImportError, AttributeError):
			# Skip modules that can't be imported or don't have the expected structure
			continue

	return models
