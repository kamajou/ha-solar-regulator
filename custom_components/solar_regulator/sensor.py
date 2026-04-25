from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SolarRegulatorCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SolarRegulatorCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SolarRegulatorConsumptionSensor(coordinator, entry),
        SolarRegulatorLimitSensor(coordinator, entry),
        SolarRegulatorStatusSensor(coordinator, entry),
        SolarRegulatorModeSensor(coordinator, entry),
    ])


class _SolarRegulatorBaseSensor(SensorEntity):
    _attr_should_poll = False

    def __init__(self, coordinator: SolarRegulatorCoordinator, entry: ConfigEntry, name: str, unique_suffix: str):
        self._coordinator = coordinator
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{unique_suffix}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Solar Regulator",
            "manufacturer": "ha-solar-regulator",
        }
        self._remove_listener = None

    async def async_added_to_hass(self):
        self._remove_listener = self._coordinator.register_update_callback(
            self.async_write_ha_state
        )

    async def async_will_remove_from_hass(self):
        if self._remove_listener:
            self._remove_listener()


class SolarRegulatorConsumptionSensor(_SolarRegulatorBaseSensor):
    """Summe aller konfigurierten Verbrauchssensoren (Eingang des Reglers)."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_icon = "mdi:home-lightning-bolt"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "Solar Regulator Gesamtverbrauch", "consumption")

    @property
    def native_value(self):
        return self._coordinator.total_consumption


class SolarRegulatorLimitSensor(_SolarRegulatorBaseSensor):
    """Aktueller Sollwert als 'x W (y%)'."""

    _attr_icon = "mdi:solar-power"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "Solar Regulator Sollwert", "limit")

    @property
    def native_value(self):
        if self._coordinator.current_limit is None:
            return None
        w = self._coordinator.current_limit
        pct = w / self._coordinator.max_power * 100
        return f"{w:.0f}W ({pct:.1f}%)"


class SolarRegulatorStatusSensor(_SolarRegulatorBaseSensor):
    """Betriebsstatus und Warnungen des Reglers."""

    _attr_icon = "mdi:information-outline"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "Solar Regulator Status", "status")

    @property
    def native_value(self):
        return self._coordinator.status


class SolarRegulatorModeSensor(_SolarRegulatorBaseSensor):
    """Aktiver Regelungsmodus."""

    _attr_icon = "mdi:cog-outline"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "Solar Regulator Modus", "mode")

    @property
    def native_value(self):
        return self._coordinator.mode


