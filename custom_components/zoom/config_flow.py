"""Config flow for Zoom Automation."""
import logging
from typing import Any, Dict

from homeassistant import config_entries
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_EXCLUDE,
    CONF_INCLUDE,
    CONF_NAME,
)
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.config_validation import multi_select
from homeassistant.util import slugify
import voluptuous as vol

from .common import ZoomOAuth2Implementation, get_contact_name, valid_external_url
from .const import (
    API,
    ATTR_COMPANY,
    ATTR_EXTERNAL,
    CONF_CONTACT_IDS_TO_MONITOR,
    CONF_CONTACT_TYPES,
    CONF_CONTACTS_TO_INCLUDE_OR_EXCLUDE,
    CONF_INCLUDE_OR_EXCLUDE,
    CONF_VERIFICATION_TOKEN,
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    ZOOM_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)


class ZoomOptionsConfigFlow(config_entries.OptionsFlow):
    """Handle Zoom options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize Zoom options flow."""
        self.config_entry = config_entry
        self._first_run = True
        self._options = {}
        self._contacts = {}

    async def async_step_init(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Manage the Zoom options."""
        if user_input:
            if user_input.get(CONF_CONTACT_TYPES):
                self._options[CONF_CONTACT_TYPES] = user_input[CONF_CONTACT_TYPES]
                return await self.async_step_include_or_exclude_contacts()

            return self.async_create_entry(title="", data={})

        options = vol.Schema(
            {
                vol.Optional(
                    CONF_CONTACT_TYPES,
                    default=self.config_entry.options.get(
                        CONF_CONTACT_TYPES,
                        [],
                    ),
                ): multi_select(
                    [ATTR_COMPANY, ATTR_EXTERNAL]  # type: ignore
                )
            }
        )

        return self.async_show_form(step_id="init", data_schema=options)

    async def async_step_include_or_exclude_contacts(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Manage the Zoom contacts included or excluded."""
        if user_input:
            if user_input.get(CONF_CONTACTS_TO_INCLUDE_OR_EXCLUDE):
                self._options[CONF_INCLUDE_OR_EXCLUDE] = user_input[
                    CONF_INCLUDE_OR_EXCLUDE
                ]
                self._options[CONF_CONTACTS_TO_INCLUDE_OR_EXCLUDE] = user_input[
                    CONF_CONTACTS_TO_INCLUDE_OR_EXCLUDE
                ]
                if user_input[CONF_INCLUDE_OR_EXCLUDE] == CONF_INCLUDE:
                    self._options[CONF_CONTACT_IDS_TO_MONITOR] = [
                        self._contacts[k]
                        for k in user_input[CONF_CONTACTS_TO_INCLUDE_OR_EXCLUDE]
                    ]
                else:
                    self._options[CONF_CONTACT_IDS_TO_MONITOR] = [
                        self._contacts[k]
                        for k in self._contacts.keys()
                        if k not in user_input[CONF_CONTACTS_TO_INCLUDE_OR_EXCLUDE]
                    ]

            return self.async_create_entry(title="", data=self._options)

        default_include_or_exclude = (
            CONF_EXCLUDE
            if self.config_entry.options.get(CONF_INCLUDE_OR_EXCLUDE) == CONF_EXCLUDE
            else CONF_INCLUDE
        )
        contacts = await self.hass.data[DOMAIN][self.config_entry.entry_id][
            API
        ].async_get_contacts(self._options[CONF_CONTACT_TYPES])

        if contacts:
            self._contacts = {
                get_contact_name(contact): contact["id"] for contact in contacts
            }

            options = vol.Schema(
                {
                    vol.Optional(
                        CONF_INCLUDE_OR_EXCLUDE,
                        default=default_include_or_exclude,
                    ): vol.All(vol.In([CONF_INCLUDE, CONF_EXCLUDE]), vol.Lower),
                    vol.Optional(
                        CONF_CONTACTS_TO_INCLUDE_OR_EXCLUDE,
                        default=self.config_entry.options.get(
                            CONF_CONTACTS_TO_INCLUDE_OR_EXCLUDE
                        ),
                    ): multi_select(
                        sorted([k for k in self._contacts.keys()])  # type: ignore
                    ),
                }
            )

            return self.async_show_form(
                step_id="include_or_exclude_contacts", data_schema=options
            )

        return await self.async_step_no_contacts()

    async def async_step_no_contacts(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Display a message that no contacts were found."""
        if self._first_run:
            self._first_run = False
            return self.async_show_form(step_id="no_contacts")

        return self.async_create_entry(title="", data=self._options)


class ZoomOAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Zoom Automation OAuth2 authentication."""

    DOMAIN = DOMAIN
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ZoomOptionsConfigFlow:
        """Get the options flow for this handler."""
        return ZoomOptionsConfigFlow(config_entry)

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    def __init__(self) -> None:
        """Intantiate config flow."""
        self._name: str = ""
        self._stored_data = {}
        super().__init__()

    async def async_step_user(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Handle a flow start."""
        assert self.hass

        if not valid_external_url(self.hass):
            return self.async_abort(reason="no_external_url")

        if (
            user_input is None
            and not await config_entry_oauth2_flow.async_get_implementations(
                self.hass, self.DOMAIN
            )
        ):
            return self.async_show_form(step_id="user", data_schema=ZOOM_SCHEMA)

        if user_input:
            self.async_register_implementation(
                self.hass,
                ZoomOAuth2Implementation(
                    self.hass,
                    DOMAIN,
                    user_input[CONF_CLIENT_ID],
                    user_input[CONF_CLIENT_SECRET],
                    OAUTH2_AUTHORIZE,
                    OAUTH2_TOKEN,
                    user_input[CONF_VERIFICATION_TOKEN],
                ),
            )

        return await self.async_step_pick_implementation()

    async def async_step_choose_name(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Require users to choose a name for each entry."""
        if not user_input:
            return self.async_show_form(
                step_id="choose_name",
                data_schema=vol.Schema({vol.Required(CONF_NAME): vol.Coerce(str)}),
            )

        self._name = user_input[CONF_NAME]
        await self.async_set_unique_id(
            f"{DOMAIN}_{slugify(self._name)}", raise_on_progress=True
        )
        self._abort_if_unique_id_configured()

        return await self.async_oauth_create_entry()

    async def async_oauth_create_entry(
        self, data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create an entry for the flow."""
        if not self._name:
            self._stored_data = data.copy()
            return await self.async_step_choose_name()

        data = self._stored_data
        self.flow_impl: ZoomOAuth2Implementation
        data.update(
            {
                CONF_NAME: self._name,
                CONF_CLIENT_ID: self.flow_impl.client_id,
                CONF_CLIENT_SECRET: self.flow_impl.client_secret,
                CONF_VERIFICATION_TOKEN: self.flow_impl._verification_token,
            }
        )
        return self.async_create_entry(title=self._name, data=data)
