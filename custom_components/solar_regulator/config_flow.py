#!/usr/bin/env python3

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
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

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_POWER_SENSORS): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", multiple=True)
        ),
        vol.Required(CONF_INVERTER_LIMIT_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["number", "input_number"])
        ),
        vol.Optional(CONF_INVERTER_MAX_POWER, default=DEFAULT_INVERTER_MAX_POWER): selector.NumberSelector(
            selector.NumberSelectorConfig(min=10, max=2000, step=10, unit_of_measurement="W")
        ),
        vol.Optional(CONF_INVERTER_MIN_POWER, default=DEFAULT_INVERTER_MIN_POWER): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=200, step=5, unit_of_measurement="W")
        ),
        vol.Optional(CONF_INTERVAL, default=DEFAULT_INTERVAL): selector.NumberSelector(
            selector.NumberSelectorConfig(min=5, max=300, step=5, unit_of_measurement="s")
        ),
        vol.Optional(CONF_MIN_CHANGE, default=DEFAULT_MIN_CHANGE): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=200, step=1, unit_of_measurement="W")
        ),
        vol.Optional(CONF_BASE_CONSUMPTION, default=DEFAULT_BASE_CONSUMPTION): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=5000, step=10, unit_of_measurement="W")
        ),
        vol.Optional(CONF_SPIKE_FILTER, default=DEFAULT_SPIKE_FILTER): selector.NumberSelector(
            selector.NumberSelectorConfig(min=50, max=5000, step=50, unit_of_measurement="W")
        ),
        vol.Optional(CONF_SPIKE_DURATION, default=DEFAULT_SPIKE_DURATION): selector.NumberSelector(
            selector.NumberSelectorConfig(min=10, max=300, step=10, unit_of_measurement="s")
        ),
        vol.Optional(CONF_ALLOWED_FEEDIN, default=DEFAULT_ALLOWED_FEEDIN): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=500, step=5, unit_of_measurement="W")
        ),
        vol.Optional(CONF_PANEL_POWER_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        ),
        vol.Optional(CONF_BATTERY_SOC_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        ),
        vol.Optional(CONF_BATTERY_FULL_THRESHOLD, default=DEFAULT_BATTERY_FULL_THRESHOLD): selector.NumberSelector(
            selector.NumberSelectorConfig(min=50, max=100, step=1, unit_of_measurement="%")
        ),
        vol.Optional(CONF_BATTERY_FULL_MARGIN, default=DEFAULT_BATTERY_FULL_MARGIN): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100, step=5, unit_of_measurement="%")
        ),
        vol.Optional(CONF_BATTERY_LOW_THRESHOLD, default=DEFAULT_BATTERY_LOW_THRESHOLD): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=80, step=5, unit_of_measurement="%")
        ),
        vol.Optional(CONF_BATTERY_LOW_OUTPUT, default=DEFAULT_BATTERY_LOW_OUTPUT): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=2000, step=10, unit_of_measurement="W")
        ),
        vol.Optional(CONF_SOLAR_FORECAST_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        ),
    }
)


class SolarRegulatorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Solar Regulator."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Solar Regulator", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(SCHEMA, {}),
            errors={},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SolarRegulatorOptionsFlow()


class SolarRegulatorOptionsFlow(config_entries.OptionsFlow):
    """Options flow – self.config_entry is injected automatically by HA."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(SCHEMA, current),
        )
