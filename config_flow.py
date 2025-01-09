from __future__ import annotations

import logging
import socket
from typing import Any

import voluptuous as vol
from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from .const import DOMAIN


def is_valid_ip(ip: str):
    try:
        socket.inet_aton(ip)
        return True
    # legal
    except socket.error:
        return False


DATA_SCHEMA = vol.Schema({("ip"): str})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        if user_input is not None and is_valid_ip(user_input["ip"]):
            return self.async_create_entry(title=user_input["ip"], data=user_input)

        errors = {}

        if user_input is not None and not is_valid_ip(user_input["ip"]):
            errors = {"ip": "Invalid IP"}

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )
