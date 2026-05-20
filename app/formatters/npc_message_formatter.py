from html import escape


def _value(value: object) -> str:
    if value is None:
        return ""
    return escape(str(value))


def format_npc_message(npc: object) -> str:
    name = _value(getattr(npc, "name", None))
    role = _value(getattr(npc, "role", None))
    description = _value(getattr(npc, "description", None))
    max_hp = _value(getattr(npc, "max_hp", None))
    current_hp = _value(getattr(npc, "current_hp", None))
    armor_class = _value(getattr(npc, "armor_class", None))
    campaign_id = _value(getattr(npc, "campaign_id", None))

    parts = [
        f"<b>NPC</b>: {name}",
        "",
        "<b>Основное</b>",
        f"Роль: {role}",
        f"Кампания: {campaign_id}",
        "",
        "<b>Боевые параметры</b>",
        f"Макс. HP: {max_hp}",
        f"Текущее HP: {current_hp}",
        f"Класс брони: {armor_class}",
        "",
        "<b>Описание</b>",
        description,
    ]

    return "\n".join(parts).strip()
