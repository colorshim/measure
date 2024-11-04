from __future__ import annotations

from typing import Any

import inquirer
from const import QUESTION_ENTITY_ID
from controller.errors import ControllerError
from homeassistant_api import Client, HomeassistantAPIError
from runner.const import QUESTION_CHARGING_DEVICE_TYPE

from .const import QUESTION_BATTERY_LEVEL_ATTRIBUTE, ChargingDeviceType
from .controller import ChargingController

DEVICE_TYPE_DOMAIN = {
    ChargingDeviceType.VACUUM_ROBOT: "vacuum",
}

ATTR_BATTERY_LEVEL = "battery_level"


class HassChargingController(ChargingController):
    def __init__(self, api_url: str, token: str) -> None:
        self.charging_device_type: ChargingDeviceType | None = None
        self.entity_id: str | None = None
        self.battery_level_attribute: str | None = None
        try:
            self.client = Client(api_url, token, cache_session=False)
            self.client.get_config()
        except HomeassistantAPIError as e:
            raise ControllerError(f"Failed to connect to HA API: {e}") from e

    def get_battery_level(self) -> int:
        """Get actual battery level of the device"""

        entity = self.client.get_entity(entity_id=self.entity_id)
        return int(entity.state.attributes[self.battery_level_attribute])

    def is_charging(self) -> bool:
        """Check if the device is currently charging"""

        entity = self.client.get_entity(entity_id=self.entity_id)
        return entity.state.state == "docked"

    def is_valid_state(self) -> bool:
        """Check if the entity is in a valid state where it is available, either charging or performing tasks"""

        entity = self.client.get_entity(entity_id=self.entity_id)
        return entity.state.state in ["docked", "cleaning", "returning", "idle", "paused"]

    def get_questions(self) -> list[inquirer.questions.Question]:
        def get_entity_list(answers: dict[str, Any]) -> list:
            domain = DEVICE_TYPE_DOMAIN.get(ChargingDeviceType(answers[QUESTION_CHARGING_DEVICE_TYPE]), "sensor")
            return get_domain_entity_list(domain)

        def get_attribute_list(answers: dict[str, Any]) -> list:
            entity = self.client.get_entity(entity_id=answers[QUESTION_ENTITY_ID])
            return sorted(entity.state.attributes.keys())

        def get_domain_entity_list(domain: str) -> list:
            entities = self.client.get_entities()
            if domain not in entities:
                return []
            found_entities = entities[domain].entities.values()
            return sorted([entity.entity_id for entity in found_entities])

        return [
            inquirer.List(
                name=QUESTION_ENTITY_ID,
                message="Select the vacuum entity",
                choices=get_entity_list,
            ),
            inquirer.List(
                name=QUESTION_BATTERY_LEVEL_ATTRIBUTE,
                message="Select the battery_level attribute",
                choices=get_attribute_list,
                ignore=lambda x: ATTR_BATTERY_LEVEL in get_attribute_list(x),
            ),
        ]

    def process_answers(self, answers: dict[str, Any]) -> None:
        self.entity_id = answers[QUESTION_ENTITY_ID]
        self.charging_device_type = answers[QUESTION_CHARGING_DEVICE_TYPE]
        self.battery_level_attribute = answers.get(QUESTION_BATTERY_LEVEL_ATTRIBUTE) or ATTR_BATTERY_LEVEL
