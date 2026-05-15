from smartx_rfid.license import LicenseManager
from app.core import LICENSE_PATH
import logging
from app.core import alerts_manager

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA00QgDyPjuscTBoWBnS1p
GReG6ysiK8eEel0BRGp4gv825GJf4LQkhdKXU78f+dh9cxIYKOlHOa2xXyTCHX2s
RbYIqaDxyop3tVoH+hZcB7oxijiyxhEYrm5Ev5Mh54nALAaP6FZJl+YHiX5OOgTu
5enor/YiYXnftzybd2S8Z6wGCDEmyRjZm03+OD3kJhuEC3l8vS6Iq0rl57CC0Jw8
2qrLJeWr6WFdQUJ6BnXjg4foA6wXdteNDU8ARh/whbd6ie3qHZzhcCncgNZqok4O
jjjIWQzhSOtKxg3DywiKAT0LIh9QReMIzLxcoSqi2LMgLbJANcrexsiJUeHEYx/l
oQIDAQAB
-----END PUBLIC KEY-----"""

# Load license string
try:
	with open(LICENSE_PATH, 'r') as f:
		LICENCE_STR = f.read()
except Exception as e:
	logging.error(f'Error loading license string: {e}')
	LICENCE_STR = None

# Initialize License Manager
license_manager = LicenseManager(
	public_key_pem=PUBLIC_KEY,
)
try:
	license_manager.load_license(LICENCE_STR)
	logging.info(f'License data: {license_manager.license_data}')
	expire_in = license_manager.expires_in()
	if expire_in is None:
		logging.error('Error to get license expire time')
	elif expire_in <= 0:
		logging.error('License has expired')
	elif expire_in <= 30:
		message = f'License will expire in {expire_in} days'
		logging.warning(message)
		if expire_in <= 7:
			alerts_manager.add_error(message)
		else:
			alerts_manager.add_warning(message)
except Exception as e:
	logging.error(f'Error loading license: {e}')
