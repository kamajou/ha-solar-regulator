from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .coordinator import SolarRegulatorCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SolarRegulatorCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SolarRegulatorSwitch(coordinator, entry)])


class SolarRegulatorSwitch(SwitchEntity, RestoreEntity):
    """Schalter zum Aktivieren/Deaktivieren des Reglers."""

    _attr_name = "Solar Regulator"
    _attr_icon = "mdi:solar-power-variant"

    def __init__(self, coordinator: SolarRegulatorCoordinator, entry: ConfigEntry):
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_switch"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Solar Regulator",
            "manufacturer": "ha-solar-regulator",
        }

    async def async_added_to_hass(self):
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._coordinator.enabled = last_state.state != "off"
        else:
            self._coordinator.enabled = True

    @property
    def is_on(self) -> bool:
        return self._coordinator.enabled

    async def async_turn_on(self, **kwargs):
        self._coordinator.enabled = True
        self.hass.async_create_task(self._coordinator._regulate())
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._coordinator.enabled = False
        self.hass.async_create_task(self._coordinator._regulate())
        self.async_write_ha_state()
