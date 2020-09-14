"""Constants for the Zoom integration."""
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.helpers.config_validation import string
import voluptuous as vol

CONTACTS = "contacts"
UNSUB = "unsub"
API = "api"
DOMAIN = "zoom"
DEFAULT_NAME = "Zoom"

HA_URL = f"/api/{DOMAIN}"

CONF_VERIFICATION_TOKEN = "verification_token"
CONF_CONTACT_TYPES = "contact_types"
ATTR_EXTERNAL = "external"
ATTR_COMPANY = "company"
CONF_CONTACTS_TO_INCLUDE_OR_EXCLUDE = "contacts_to_include_or_exclude"
CONF_CONTACT_IDS_TO_MONITOR = "contacts_to_monitor"
CONF_INCLUDE_OR_EXCLUDE = "include_or_exclude"
ATTR_EXCLUDE = "exclude"
ATTR_INCLUDE = "include"

OAUTH2_AUTHORIZE = "https://zoom.us/oauth/authorize"
OAUTH2_TOKEN = "https://zoom.us/oauth/token"

BASE_URL = "https://api.zoom.us/v2/"
USER_PROFILE_URL = "users/me"
USER_PROFILE_COORDINATOR = "user_profile_coordinator"
CONTACT_LIST_URL = "chat/users/me/contacts"
CONTACT_LIST_COORDINATOR = "contact_list_coordinator"

ZOOM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLIENT_ID): vol.Coerce(str),
        vol.Required(CONF_CLIENT_SECRET): vol.Coerce(str),
        vol.Required(CONF_VERIFICATION_TOKEN): vol.Coerce(str),
    }
)

ATTR_EVENT = "event"
ATTR_PAYLOAD = "payload"
ATTR_OBJECT = "object"
ATTR_ID = "id"
ATTR_CONNECTIVITY_STATUS = "presence_status"

CONNECTIVITY_EVENT = "user.presence_status_updated"
CONNECTIVITY_STATUS = [ATTR_PAYLOAD, ATTR_OBJECT, ATTR_CONNECTIVITY_STATUS]
CONNECTIVITY_ID = [ATTR_PAYLOAD, ATTR_OBJECT, ATTR_ID]
CONNECTIVITY_STATUS_OFF = "Available"

HA_ZOOM_EVENT = f"{DOMAIN}_webhook"

WEBHOOK_RESPONSE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_EVENT): string, vol.Required(ATTR_PAYLOAD): dict}
)
