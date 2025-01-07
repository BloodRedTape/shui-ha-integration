from typing import Callable, Any
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import PERCENTAGE
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from .shui import Shui3dPrinter
from .const import PRINTER_PORT, PRINTER_IP
import logging

_LOGGER = logging.getLogger(__name__)


def log(message: str):
    _LOGGER.info(message)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""

    printer = Shui3dPrinter(PRINTER_IP, PRINTER_PORT, log)

    def updater():
        hass.add_job(printer.ensure_update())

    add_entities(
        [
            PrinterSensor(
                updater,
                printer.bed_temp,
                "Bed Temp",
                "bed temp id",
                UnitOfTemperature.CELSIUS,
                "mdi:printer-3d",
            ),
            PrinterSensor(
                updater,
                printer.target_bed_temp,
                "Target Bed Temp",
                "target bed temp id",
                UnitOfTemperature.CELSIUS,
                "mdi:printer-3d",
            ),
            PrinterSensor(
                updater,
                printer.extruder_temp,
                "Extruder Temp",
                "extruder temp id",
                UnitOfTemperature.CELSIUS,
                "mdi:printer-3d-nozzle",
            ),
            PrinterSensor(
                updater,
                printer.target_extruder_temp,
                "Target Extruder Temp",
                "target extruder temp id",
                UnitOfTemperature.CELSIUS,
                "mdi:printer-3d-nozzle",
            ),
            PrinterSensor(
                updater,
                printer.status,
                "Connection",
                "connection id",
                "",
                "mdi:access-point-network",
            ),
            PrinterSensor(
                updater,
                printer.print_status,
                "Print Status",
                "print status id",
                "",
                "mdi:state-machine",
            ),
            PrinterSensor(
                updater,
                printer.print_progress,
                "Print Progress",
                "print progress id",
                PERCENTAGE,
                "mdi:percent-outline",
            ),
        ]
    )


class PrinterSensor(SensorEntity):
    _getter: Callable[[], Any]
    _updater: Callable[[], None]
    _unit: str
    _icon: str

    def __init__(
        self,
        updater: Callable[[], None],
        getter: Callable[[], Any],
        name: str,
        id: str,
        unit: str,
        icon: str,
    ):
        self._attr_unique_id = id
        self._attr_name = name
        self._getter = getter
        self._updater = updater
        self._unit = unit
        self._icon = icon

    def update(self):
        self._updater()

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
