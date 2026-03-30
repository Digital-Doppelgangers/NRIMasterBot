import json
from typing import Any, Dict

REQUIRED_TOP_LEVEL_KEYS = {
    "meta",
    "identity",
    "build",
    "base_stats",
    "attributes_mods",
    "abilities",
    "backstory",
}


def extract_json_from_text(raw_text: str) -> Dict[str, Any]:
    text = raw_text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    return json.loads(text)


def validate_character_data(data: Dict[str, Any]) -> None:
    missing = REQUIRED_TOP_LEVEL_KEYS - data.keys()
    if missing:
        raise ValueError(f"В JSON не хватает ключей: {', '.join(sorted(missing))}")

    if not isinstance(data["identity"], dict):
        raise ValueError("Поле identity должно быть объектом")

    if not isinstance(data["build"], dict):
        raise ValueError("Поле build должно быть объектом")

    if not isinstance(data["base_stats"], dict):
        raise ValueError("Поле base_stats должно быть объектом")

    if not isinstance(data["attributes_mods"], dict):
        raise ValueError("Поле attributes_mods должно быть объектом")

    if not isinstance(data["abilities"], list):
        raise ValueError("Поле abilities должно быть списком")

    if not isinstance(data["backstory"], dict):
        raise ValueError("Поле backstory должно быть объектом")


def parse_character_response(raw_text: str) -> Dict[str, Any]:
    data = extract_json_from_text(raw_text)
    validate_character_data(data)
    return data