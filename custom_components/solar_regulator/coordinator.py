import logging
import time
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_POWER_SENSORS,
    CONF_INVERTER_LIMIT_ENTITY,
    CONF_INVERTER_MAX_POWER,
    CONF_INVERTER_MIN_POWER,
    CONF_INTERVAL,
    CONF_MIN_CHANGE,
    CONF_BASE_CONSUMPTION,
    CONF_SPIKE_FILTER,
    CONF_SPIKE_DURATION,
    CONF_ALLOWED_FEEDIN,
    CONF_PANEL_POWER_SENSOR,
    CONF_BATTERY_SOC_SENSOR,
    CONF_BATTERY_FULL_THRESHOLD,
    CONF_BATTERY_FULL_MARGIN,
    CONF_BATTERY_LOW_THRESHOLD,
    CONF_BATTERY_LOW_OUTPUT,
    CONF_SOLAR_FORECAST_SENSOR,
    DEFAULT_INVERTER_MAX_POWER,
    DEFAULT_INVERTER_MIN_POWER,
    DEFAULT_INTERVAL,
    DEFAULT_MIN_CHANGE,
    DEFAULT_BASE_CONSUMPTION,
    DEFAULT_SPIKE_FILTER,
    DEFAULT_SPIKE_DURATION,
    DEFAULT_ALLOWED_FEEDIN,
    DEFAULT_BATTERY_FULL_THRESHOLD,
    DEFAULT_BATTERY_FULL_MARGIN,
    DEFAULT_BATTERY_LOW_THRESHOLD,
    DEFAULT_BATTERY_LOW_OUTPUT,
)

_LOGGER = logging.getLogger(__name__)


class SolarRegulatorCoordinator:

    def __init__(self, hass: HomeAssistant, config: dict):
        self.hass = hass

        self._power_sensors: list[str] = config[CONF_POWER_SENSORS]
        self._limit_entity: str = config[CONF_INVERTER_LIMIT_ENTITY]
        self._max_power: float = float(config.get(CONF_INVERTER_MAX_POWER, DEFAULT_INVERTER_MAX_POWER))
        self.max_power: float = self._max_power
        self._min_power: float = float(config.get(CONF_INVERTER_MIN_POWER, DEFAULT_INVERTER_MIN_POWER))
        self._interval: int = int(config.get(CONF_INTERVAL, DEFAULT_INTERVAL))
        self._min_change: float = float(config.get(CONF_MIN_CHANGE, DEFAULT_MIN_CHANGE))
        self._base_consumption: float = float(config.get(CONF_BASE_CONSUMPTION, DEFAULT_BASE_CONSUMPTION))
        self._spike_filter: float = float(config.get(CONF_SPIKE_FILTER, DEFAULT_SPIKE_FILTER))
        self._spike_duration: float = float(config.get(CONF_SPIKE_DURATION, DEFAULT_SPIKE_DURATION))
        self._allowed_feedin: float = float(config.get(CONF_ALLOWED_FEEDIN, DEFAULT_ALLOWED_FEEDIN))
        self._last_sensor_values: dict[str, float] = {}
        self._spike_pending: dict[str, tuple[float, float]] = {}  # entity_id → (value, timestamp)

        self._panel_power_sensor: str | None = config.get(CONF_PANEL_POWER_SENSOR) or None
        self._battery_soc_sensor: str | None = config.get(CONF_BATTERY_SOC_SENSOR) or None
        self._battery_full_threshold: float = float(config.get(CONF_BATTERY_FULL_THRESHOLD, DEFAULT_BATTERY_FULL_THRESHOLD))
        self._battery_full_margin: float = float(config.get(CONF_BATTERY_FULL_MARGIN, DEFAULT_BATTERY_FULL_MARGIN))
        self._battery_low_threshold: float = float(config.get(CONF_BATTERY_LOW_THRESHOLD, DEFAULT_BATTERY_LOW_THRESHOLD))
        self._battery_low_output: float = float(config.get(CONF_BATTERY_LOW_OUTPUT, DEFAULT_BATTERY_LOW_OUTPUT))
        self._solar_forecast_sensor: str | None = config.get(CONF_SOLAR_FORECAST_SENSOR) or None

        self._current_limit: float | None = None
        self._disabled_output_sent: bool = False
        self._unsub = None
        self._listeners: list = []

        # Public state – readable by sensor/switch entities
        self.enabled: bool = True
        self.total_consumption: float | None = None
        self.current_limit: float | None = None
        self.status: str = "Warte auf ersten Regelzyklus"
        self.mode: str = "Warte auf ersten Regelzyklus"

    def register_update_callback(self, callback) -> callable:
        self._listeners.append(callback)
        def remove():
            if callback in self._listeners:
                self._listeners.remove(callback)
        return remove

    def start(self):
        _LOGGER.info(
            "Solar Regulator gestartet: Sensoren=%s, Limit-Entity=%s, Intervall=%ds",
            self._power_sensors,
            self._limit_entity,
            self._interval,
        )
        self.hass.async_create_task(self._regulate())
        self._unsub = async_track_time_interval(
            self.hass,
            self._regulate,
            timedelta(seconds=self._interval),
        )

    def stop(self):
        if self._unsub:
            self._unsub()
            self._unsub = None
        _LOGGER.info("Solar Regulator gestoppt.")

    async def _regulate(self, _now=None):
        try:
            await self._regulate_safe()
        except Exception as err:
            _LOGGER.exception("Fehler im Regelzyklus: %s", err)
            self.status = f"Fehler: {err}"
            for cb in self._listeners:
                cb()

    async def _regulate_safe(self):

        # Regler deaktiviert → Minimalleistung einmalig ausgeben, danach nicht mehr eingreifen
        if not self.enabled:
            if not self._disabled_output_sent:
                setpoint_pct = round(self._min_power / self._max_power * 100.0, 1)
                await self.hass.services.async_call(
                    "number",
                    "set_value",
                    {"entity_id": self._limit_entity, "value": setpoint_pct},
                    blocking=True,
                )
                self._current_limit = self._min_power
                self.current_limit = self._min_power
                self._disabled_output_sent = True
                _LOGGER.info("Regler deaktiviert – Minimalleistung %.0fW gesetzt.", self._min_power)
            self.status = "Regler deaktiviert"
            self.mode = "Deaktiviert"
            for cb in self._listeners:
                cb()
            return

        # Regler aktiv → Flag zurücksetzen damit beim nächsten Deaktivieren wieder einmalig ausgegeben wird
        self._disabled_output_sent = False

        # 1. Summe aller Verbrauchssensoren (mit Spike-Filter)
        total = 0.0
        unavailable: list[str] = []
        spikes: list[str] = []

        for entity_id in self._power_sensors:
            state = self.hass.states.get(entity_id)
            if state is None or state.state in ("unavailable", "unknown"):
                _LOGGER.warning("Sensor '%s' nicht verfügbar, überspringe.", entity_id)
                unavailable.append(entity_id)
                continue
            try:
                value = float(state.state)
            except ValueError:
                _LOGGER.warning("Sensor '%s' liefert keinen numerischen Wert: %s", entity_id, state.state)
                unavailable.append(entity_id)
                continue

            last = self._last_sensor_values.get(entity_id)
            if last is not None and value - last > self._spike_filter:
                pending = self._spike_pending.get(entity_id)
                if pending is not None and (time.monotonic() - pending[1]) >= self._spike_duration:
                    # Wert hält lange genug an → als echte Last akzeptieren
                    _LOGGER.info(
                        "Spike bestätigt: '%s' %.0fW seit %.0fs → akzeptiert",
                        entity_id, value, self._spike_duration,
                    )
                    self._spike_pending.pop(entity_id)
                else:
                    # Noch nicht lang genug → weiter filtern
                    if pending is None:
                        self._spike_pending[entity_id] = (value, time.monotonic())
                    spikes.append(entity_id)
                    value = last
            else:
                self._spike_pending.pop(entity_id, None)

            self._last_sensor_values[entity_id] = value
            total += value

        total += self._base_consumption
        self.total_consumption = round(total, 1)

        # Alle Sensoren nicht verfügbar → Gerät nicht anfassen, nur Status aktualisieren
        if unavailable and len(unavailable) == len(self._power_sensors):
            self.status = "Keine Sensoren verfügbar"
            for cb in self._listeners:
                cb()
            return

        # 2. Aktuelles Limit lesen (beim ersten Durchlauf)
        # Entity liefert Prozent (0–100) → intern in Watt umrechnen
        # force_first_output: beim ersten Zyklus immer ausgeben, unabhängig von min_change
        force_first_output = False
        if self._current_limit is None:
            limit_state = self.hass.states.get(self._limit_entity)
            if limit_state and limit_state.state not in ("unavailable", "unknown"):
                try:
                    self._current_limit = float(limit_state.state) * self._max_power / 100.0
                except ValueError:
                    self._current_limit = self._max_power
            else:
                self._current_limit = self._max_power
            self.current_limit = self._current_limit
            force_first_output = True

        # 3. Sollwert = Verbrauchssumme (Basis)
        setpoint = total

        # 4. Batterieoptimierung
        battery_soc = self._read_optional_float(self._battery_soc_sensor, "Batterie-SOC")
        panel_power = self._read_optional_float(self._panel_power_sensor, "Panelleistung")

        if battery_soc is not None and battery_soc <= self._battery_low_threshold:
            setpoint = self._battery_low_output
            self.mode = "Batterie laden"
            _LOGGER.debug(
                "Batterie niedrig: SOC=%.0f%% ≤ %.0f%% → Sollwert=%.0fW",
                battery_soc, self._battery_low_threshold, setpoint,
            )
        elif battery_soc is not None and battery_soc >= self._battery_full_threshold:
            if panel_power is not None and panel_power > 0:
                floored = int(panel_power // 200) * 200
                setpoint = float(max(total, max(200, floored - 200)))
                self.mode = "Batterie voll · Panel-Formel"
                _LOGGER.debug(
                    "Batterieoptimierung: SOC=%.0f%%, Panel=%.0fW → Sollwert=%.0fW",
                    battery_soc, panel_power, setpoint,
                )
            else:
                setpoint *= 1.0 + (self._battery_full_margin / 100.0)
                self.mode = "Batterie voll · Verbrauch + Marge"
                _LOGGER.debug(
                    "Batterieoptimierung: SOC=%.0f%% (voll, kein Panel) → Sollwert=%.1fW (+%.0f%%)",
                    battery_soc, setpoint, self._battery_full_margin,
                )
        else:
            self.mode = "Normal"

        # 5. Forecast-Optimierung: morgen wenig Sonne → heute mehr laden (TODO)
        forecast = self._read_optional_float(self._solar_forecast_sensor, "Solar-Forecast")
        if forecast is not None:
            _LOGGER.debug("Solar-Forecast: %.0fW (Optimierung TODO)", forecast)

        # 6. Auf Hardware-Grenzen begrenzen
        setpoint = max(self._min_power, min(self._max_power, round(setpoint, 1)))

        # 7. Ausgabe-Entscheidung:
        #    - Sofort reagieren wenn Einspeisung die erlaubte Grenze überschreiten würde
        #    - Sonst nur wenn Änderung >= min_change
        feedin_exceeded = setpoint < self._current_limit - self._allowed_feedin
        should_update = force_first_output or feedin_exceeded or abs(setpoint - self._current_limit) >= self._min_change

        if not should_update:
            _LOGGER.debug(
                "Solar Regulator: Verbrauch=%.1fW, Sollwert=%.1fW, Δ=%.1fW → kein Eingriff",
                total, setpoint, abs(setpoint - self._current_limit),
            )
        else:
            _LOGGER.info(
                "Solar Regulator: Verbrauch=%.1fW → Limit %.1f→%.1fW",
                total, self._current_limit, setpoint,
            )
            setpoint_pct = round(setpoint / self._max_power * 100.0, 1)
            await self.hass.services.async_call(
                "number",
                "set_value",
                {"entity_id": self._limit_entity, "value": setpoint_pct},
                blocking=True,
            )
            self._current_limit = setpoint
            self.current_limit = setpoint

        # Status setzen – Probleme zuerst, sonst "Aktiv"
        if unavailable:
            self.status = f"Sensor nicht verfügbar: {', '.join(unavailable)}"
        elif spikes:
            self.status = f"Spike gefiltert: {', '.join(spikes)}"
        else:
            self.status = "Aktiv"

        for cb in self._listeners:
            cb()

    def _read_optional_float(self, entity_id: str | None, name: str) -> float | None:
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unavailable", "unknown"):
            _LOGGER.debug("%s-Sensor '%s' nicht verfügbar.", name, entity_id)
            return None
        try:
            return float(state.state)
        except ValueError:
            _LOGGER.warning("%s-Sensor '%s' liefert keinen numerischen Wert: %s", name, entity_id, state.state)
            return None
