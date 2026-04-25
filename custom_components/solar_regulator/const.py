DOMAIN = "solar_regulator"

# Config keys
CONF_POWER_SENSORS = "power_sensors"
CONF_INVERTER_LIMIT_ENTITY = "inverter_limit_entity"
CONF_INVERTER_MAX_POWER = "inverter_max_power"
CONF_INVERTER_MIN_POWER = "inverter_min_power"
CONF_INTERVAL = "interval"
CONF_MIN_CHANGE = "min_change"
CONF_BASE_CONSUMPTION = "base_consumption"
CONF_SPIKE_FILTER = "spike_filter"
CONF_SPIKE_DURATION = "spike_duration"
CONF_ALLOWED_FEEDIN = "allowed_feedin"
CONF_PANEL_POWER_SENSOR = "panel_power_sensor"
CONF_BATTERY_SOC_SENSOR = "battery_soc_sensor"
CONF_BATTERY_FULL_THRESHOLD = "battery_full_threshold"
CONF_BATTERY_FULL_MARGIN = "battery_full_margin"
CONF_SOLAR_FORECAST_SENSOR = "solar_forecast_sensor"

# Defaults
DEFAULT_INVERTER_MAX_POWER = 800
DEFAULT_INVERTER_MIN_POWER = 10
DEFAULT_INTERVAL = 30           # Sekunden
DEFAULT_MIN_CHANGE = 20         # Watt – Mindestabstand zum vorherigen Sollwert
DEFAULT_BASE_CONSUMPTION = 0    # Watt – fixer Grundverbrauch (immer addiert)
DEFAULT_SPIKE_FILTER = 500      # Watt – max. erlaubter Anstieg pro Sensor pro Zyklus
DEFAULT_SPIKE_DURATION = 60    # Sekunden – wie lange ein Spike anhalten muss um akzeptiert zu werden
DEFAULT_ALLOWED_FEEDIN = 0      # Watt – erlaubte Einspeisung bevor sofort reagiert wird
DEFAULT_BATTERY_FULL_THRESHOLD = 90  # % – ab hier Marge anwenden
DEFAULT_BATTERY_FULL_MARGIN = 20     # % – Marge über Verbrauch wenn Akku voll
