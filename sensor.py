import logging
from typing import Any, Callable, Awaitable, List

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .shui import Shui3dPrinter, Shui3dPrinterConnectionStatus, Shui3dPrintStatus

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
            PrinterSensor(
                printer.ensure_update,
                printer.bed_temp,
                "Bed Temp",
                "bed temp id",
                UnitOfTemperature.CELSIUS,
                "mdi:printer-3d",
                SensorDeviceClass.TEMPERATURE,
            ),
            PrinterSensor(
                printer.ensure_update,
                printer.target_bed_temp,
                "Target Bed Temp",
                "target bed temp id",
                UnitOfTemperature.CELSIUS,
                "mdi:printer-3d",
                SensorDeviceClass.TEMPERATURE,
            ),
            PrinterSensor(
                printer.ensure_update,
                printer.extruder_temp,
                "Extruder Temp",
                "extruder temp id",
                UnitOfTemperature.CELSIUS,
                "mdi:printer-3d-nozzle",
                SensorDeviceClass.TEMPERATURE,
            ),
            PrinterSensor(
                printer.ensure_update,
                printer.target_extruder_temp,
                "Target Extruder Temp",
                "target extruder temp id",
                UnitOfTemperature.CELSIUS,
                "mdi:printer-3d-nozzle",
                SensorDeviceClass.TEMPERATURE,
            ),
            PrinterEnum(
                printer.ensure_update,
                printer.status,
                "Connection",
                "connection id",
                "mdi:access-point-network",
                [member.name for member in Shui3dPrinterConnectionStatus],
            ),
            PrinterEnum(
                printer.ensure_update,
                printer.print_status,
                "Print Status",
                "print status id",
                "mdi:state-machine",
                [member.name for member in Shui3dPrintStatus],
            ),
            PrinterSensor(
                printer.ensure_update,
                printer.print_progress,
                "Print Progress",
                "print progress id",
                PERCENTAGE,
                "mdi:percent-outline",
                None,
            ),
        ]
    )


class PrinterSensor(SensorEntity):
    _getter: Callable[[], Any]
    _updater: Callable[[], Awaitable[Any]]
    _unit: str
    _icon: str
    _device_class: SensorDeviceClass | None

    def __init__(
        self,
        updater: Callable[[], Awaitable[Any]],
        getter: Callable[[], Any],
        name: str,
        id: str,
        unit: str,
        icon: str,
        deivce_class: SensorDeviceClass | None,
    ):
        self._attr_unique_id = id
        self._attr_name = name
        self._getter = getter
        self._updater = updater
        self._unit = unit
        self._icon = icon
        self._device_class = deivce_class

    async def async_update(self):
        await self._updater()

    @property
    def icon(self):
        return self._icon

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return self._unit

    # Самое важное поле, значение объекта.
    @property
    def state(self):
        return self._getter()

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return self._device_class


class PrinterBinarySensor(BinarySensorEntity):
    _getter: Callable[[], bool]
    _updater: Callable[[], Awaitable[Any]]
    _icon: str
    _device_class: BinarySensorDeviceClass | None

    def __init__(
        self,
        updater: Callable[[], Awaitable[Any]],
        getter: Callable[[], Any],
        name: str,
        id: str,
        icon: str,
        deivce_class: BinarySensorDeviceClass | None,
    ):
        self._attr_unique_id = id
        self._attr_name = name
        self._getter = getter
        self._updater = updater
        self._icon = icon
        self._device_class = deivce_class

    async def async_update(self):
        await self._updater()

    @property
    def icon(self):
        return self._icon

    @property
    def is_on(self):
        return self._getter()

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        return self._device_class


class PrinterEnum(SensorEntity):
    _getter: Callable[[], bool]
    _updater: Callable[[], Awaitable[Any]]
    _icon: str
    _options: List[str]

    def __init__(
        self,
        updater: Callable[[], Awaitable[Any]],
        getter: Callable[[], Any],
        name: str,
        id: str,
        icon: str,
        options: List[str],
    ):
        self._attr_unique_id = id
        self._attr_name = name
        self._getter = getter
        self._updater = updater
        self._icon = icon
        self._options = options

    async def async_update(self):
        await self._updater()

    @property
    def icon(self):
        return self._icon

    @property
    def state(self):
        return self._getter()

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.ENUM

    @property
    def options(self):
        return self._options
