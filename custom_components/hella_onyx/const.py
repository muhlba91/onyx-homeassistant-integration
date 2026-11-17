"""Constants for the ONYX integration."""

DOMAIN = "hella_onyx"

CONF_FINGERPRINT = "fingerprint"
CONF_LOCAL_ADDRESS = "local_address"
CONF_MIN_DIM_DURATION = "min_dim_duration"
CONF_MAX_DIM_DURATION = "max_dim_duration"
CONF_ADDITIONAL_DELAY = "additional_delay"
CONF_INTERPOLATION_FREQUENCY = "interpolation_frequency"
CONF_CLOSED_TOLERANCE = "closed_tolerance"
CONF_MOVING_TIMEOUT = "moving_timeout"

DEFAULT_SCAN_INTERVAL = 60
DEFAULT_ADDITIONAL_DELAY = 1000
DEFAULT_MIN_DIM_DURATION = 200
DEFAULT_MAX_DIM_DURATION = 2000
DEFAULT_INTERPOLATION_FREQUENCY = 5
DEFAULT_CLOSED_TOLERANCE = 3
DEFAULT_MOVING_TIMEOUT = 180
MIN_INTERPOLATION_FREQUENCY = 0
MAX_INTERPOLATION_FREQUENCY = 10
MIN_CLOSED_TOLERANCE = 0
MAX_CLOSED_TOLERANCE = 20
# above the longest command (two attempts and the backoff, about 21 s)
MIN_MOVING_TIMEOUT = 30
MAX_MOVING_TIMEOUT = 3600
MIN_ADDITIONAL_DELAY = 0
MAX_ADDITIONAL_DELAY = 20000
MIN_DIM_DURATION = 0
MAX_DIM_DURATION = 65535
# the documented color temperature range of RGBW lights, in Kelvin
DEFAULT_MIN_COLOR_TEMPERATURE = 2700
DEFAULT_MAX_COLOR_TEMPERATURE = 10500
# the color mode of an RGBW light showing a white tone
COLOR_MODE_TEMPERATURE = "temperature"

SNAPSHOT_TIMEOUT = 30
# the longest wait (in s) for the response to one attempt of a command
COMMAND_TIMEOUT = 10
# the randomized backoff (in s) before the single retry of a failed command
COMMAND_RETRY_DELAY_MIN = 0.5
COMMAND_RETRY_DELAY_MAX = 1.0
STREAM_RESTART_DELAY = 60
STREAM_CHECK_INTERVAL = 10
# the ONYX.CENTER sends a pulse every 30 seconds; three missed pulses
STREAM_SILENCE_TIMEOUT = 90

# the listener contexts of the update entity and the automation switches
UPDATE_CONTEXT = "update"
AUTOMATION_CONTEXT = "automations"
# the longest expected installation of an ONYX.CENTER update, in seconds
UPDATE_INSTALL_TIMEOUT = 1800
