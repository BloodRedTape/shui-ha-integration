from homeassistant.components.button import ButtonEntity
from typing import Callable, Awaitable, Any
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from .shui import Shui3dPrinter
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)


def log(message: str):
    _LOGGER.info(message)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    printer: Shui3dPrinter = config_entry.runtime_data

    if printer is None or not isinstance(printer, Shui3dPrinter):
        _LOGGER.error(
            "config_entry.runtime_data does not containt Shui3dPrinter instance"
        )
        return
    async_add_entities(
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

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "shui_3d_printer")},
            "name": "Two Trees Bluer",
            "sw_version": "shui",
            "model": "Bluer",
            "manufacturer": "Two Trees",
        }
