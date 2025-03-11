from homeassistant.components.number import NumberEntity, NumberDeviceClass
import logging
from typing import Any, Callable, Awaitable, List

from .shui import Shui3dPrinter, Shui3dPrinterConnectionStatus, Shui3dPrintStatus
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    printer: Shui3dPrinter = config_entry.runtime_data

    if printer is None or not isinstance(printer, Shui3dPrinter):
        LOGGER.error(
            "config_entry.runtime_data does not containt Shui3dPrinter instance"
        )
        return

    async_add_entities(
        [
            PrinterNumber(
                printer.ensure_update,
                printer.target_bed_temp,
                printer.set_target_bed_temp,
                "Target Bed Temp",
                "target bed temp id",
                UnitOfTemperature.CELSIUS,
                "mdi:printer-3d",
                NumberDeviceClass.TEMPERATURE,
                0,
                80,
            ),
            PrinterNumber(
                printer.ensure_update,
                printer.target_extruder_temp,
                printer.set_target_extruder_temp,
                "Target Extruder Temp",
                "target extruder temp id",
                UnitOfTemperature.CELSIUS,
                "mdi:printer-3d-nozzle",
                NumberDeviceClass.TEMPERATURE,
                0,
                250,
            ),
        ]
    )


class PrinterNumber(NumberEntity):
    _getter: Callable[[], Any]
    _setter: Callable[[float], Any]
    _updater: Callable[[], Awaitable[Any]]
    _min: float
    _max: float
    _unit: str
    _icon: str
    _device_class: NumberDeviceClass | None

    def __init__(
        self,
        updater: Callable[[], Awaitable[Any]],
        getter: Callable[[], Any],
        setter: Callable[[float], Any],
        name: str,
        id: str,
        unit: str,
        icon: str,
        deivce_class: NumberDeviceClass | None,
        min: float,
        max: float,
    ):
        self._attr_unique_id = id
        self._attr_name = name
        self._getter = getter
        self._setter = setter
        self._updater = updater
        self._unit = unit
        self._icon = icon
        self._device_class = deivce_class
        self._min = min
        self._max = max

    async def async_update(self):
        await self._updater()

    async def async_set_native_value(self, value: float) -> None:
        await self._setter(value)

        self.schedule_update_ha_state()

    @property
    def native_value(self):
        return self._getter()

    @property
    def mode(self):
        return "box"

    @property
    def native_min_value(self):
        return self._min

    @property
    def native_max_value(self):
        return self._max

    @property
    def icon(self):
        return self._icon

    @property
    def native_unit_of_measurement(self) -> str:
        return self._unit

    @property
    def device_class(self) -> NumberDeviceClass | None:
        return self._device_class

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, "shui_3d_printer")}}
