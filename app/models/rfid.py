"""
RFID models for SMARTX Connector.

Defines the Tag and Event models for storing RFID reader data
with proper indexing and relationships.
"""

from sqlalchemy import Column, Index, Integer, String, Text

from smartx_rfid.models import Base, BaseMixin


class Tag(Base, BaseMixin):
	"""
	RFID Tag model for storing tag read events.

	Stores information about RFID tags detected by readers,
	including EPC, TID, antenna, and signal strength data.
	"""

	__tablename__ = 'tags'

	# Primary key
	id = Column(Integer, primary_key=True, autoincrement=True)

	# Device identification
	device = Column(String(100), nullable=False)

	# RFID data fields
	epc = Column(String(24), nullable=False)

	tid = Column(String(24), nullable=True)

	ant = Column(Integer, nullable=True)
	rssi = Column(Integer, nullable=True)

	# Indexes for optimal query performance
	__table_args__ = (
		# Composite index for device + epc (most common query pattern)
		Index('ix_tags_device_epc', 'device', 'epc'),
		# Individual indexes
		Index('ix_tags_device', 'device'),
		Index('ix_tags_tid', 'tid'),
		Index('ix_tags_epc', 'epc'),
	)


class Event(Base, BaseMixin):
	"""
	RFID Event model for storing system and reader events.

	Stores various types of events from RFID readers and the system,
	including errors, status changes, and operational events.
	"""

	__tablename__ = 'events'

	# Primary key
	id = Column(Integer, primary_key=True, autoincrement=True)

	# Device identification
	device = Column(String(100), nullable=False)

	# Event classification
	event_type = Column(String(50), nullable=False)

	# Event data
	event_data = Column(Text, nullable=False)

	# Indexes for optimal query performance
	__table_args__ = (
		# Individual indexes
		Index('ix_events_device', 'device'),
		Index('ix_events_event_type', 'event_type'),
		Index('ix_events_created_at', 'created_at'),
		# Composite indexes
		Index('ix_events_device_type', 'device', 'event_type'),
	)
