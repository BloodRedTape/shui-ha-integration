from homeassistant.components.button import ButtonEntity
from typing import Callable, Awaitable, Any
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from .shui import Shui3dPrinter
from .const import PRINTER_IP, PRINTER_PORT
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

    add_entities(
        [
            PrinterButton(
                printer.beep,
                "Locate printer",
                "locate printer id",
                "mdi:crosshairs-question",
            ),
        ]
    )


class PrinterButton(ButtonEntity):
    _icon: str
    _press: Callable[[], Awaitable[Any]]

    def __init__(
        self,
        press: Callable[[], Awaitable[Any]],
        name: str,
        id: str,
        icon: str,
    ):
        self._attr_unique_id = id
        self._attr_name = name
        self._icon = icon
        self._press = press

    async def async_press(self) -> None:
        await self._press()
