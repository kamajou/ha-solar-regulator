import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_INTERVAL
from .coordinator import SolarRegulatorCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Setup via configuration.yaml (nicht verwendet, nur Config Flow)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup des Solar Regulators aus einem Config Entry."""
    hass.data.setdefault(DOMAIN, {})

    # Merge data + options (options überschreiben data bei Änderungen)
    config = {**entry.data, **entry.options}

    coordinator = SolarRegulatorCoordinator(hass, config)
    coordinator.start()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "switch"])

    # Bei Optionsänderungen neu starten
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    _LOGGER.info("Solar Regulator erfolgreich eingerichtet.")
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Reloader wenn Optionen geändert werden."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Stoppe den Regler beim Entfernen."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "switch"])
    coordinator: SolarRegulatorCoordinator = hass.data[DOMAIN].pop(entry.entry_id, None)
    if coordinator:
        coordinator.stop()
    return unload_ok
