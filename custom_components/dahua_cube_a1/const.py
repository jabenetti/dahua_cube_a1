"""Constants for the Dahua Cube A1 integration."""

DOMAIN = "dahua_cube_a1"
CONF_CAMERAS = "cameras"          # list of IPs
CONF_PROXY_PORT = "proxy_port"
CONF_USERNAME = "username"        # shared for cameras + proxy Digest
CONF_PASSWORD = "password"

DEFAULT_PROXY_PORT = 8080
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"
DEFAULT_NAME = "Dahua Camera"