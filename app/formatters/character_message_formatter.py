from html import escape

ABILITY_TYPE_LABELS = {
    "attack": "Атака",
    "control": "Контроль",
    "strong_attack": "Сильная атака",
    "support": "Поддержка",
}

LIMIT_LABELS = {
    "at_will": "Без ограничений",
    "1/combat": "1 раз за бой",
    "2/short_rest": "2 раза до короткого отдыха",
    "1/rest": "1 раз за отдых",
}

RANGE_SHAPE_LABELS = {
    "touch": "касание",
    "melee": "ближняя",
    "ranged": "дистанционная",
    "cone": "конус",
    "line": "линия",
    "sphere": "сфера",
}

CONTROL_TYPE_LABELS = {
    "charm": "очарование",
    "blind": "ослепление",
    "stun": "оглушение",
    "fear": "страх",
    "slow": "замедление",
    "silence": "немота",
    "push": "отталкивание",
    "prone": "сбит с ног",
}

SUPPORT_TYPE_LABELS = {
    "heal": "Лечение",
    "buff_roll": "Усиление броска",
    "buff_damage": "Усиление урона",
    "buff_to_hit": "Бонус к попаданию",
    "extra_action": "Дополнительное действие",
    "cleanse": "Снятие эффектов",
}

DAMAGE_TYPE_LABELS = {
    "slashing": "рубящий",
    "piercing": "колющий",
    "bludgeoning": "дробящий",
    "fire": "огонь",
    "cold": "холод",
    "lightning": "молния",
    "poison": "яд",
    "acid": "кислота",
    "psychic": "психический",
    "necrotic": "некротический",
    "radiant": "сияние",
    "thunder": "гром",
}

ATTRIBUTE_LABELS = {
    "str": "СИЛ",
    "dex": "ЛОВ",
    "con": "ТЕЛ",
    "int": "ИНТ",
    "wis": "МДР",
    "cha": "ХАР",
}

GENDER_LABELS = {
    "male": "Мужской",
    "female": "Женский",
    "other": "Другой",
}


def display(value: object, fallback: str = "—") -> str:
    if value is None:
        return fallback
    text = str(value)
    if not text:
        return fallback
    return text


def format_ability(ability: dict) -> str:
    name = escape(display(ability.get("name"), "-"))
    ability_type = ABILITY_TYPE_LABELS.get(ability.get("type"), display(ability.get("type")))
    limit = LIMIT_LABELS.get(ability.get("limit"), display(ability.get("limit")))
    bonus_ability = ATTRIBUTE_LABELS.get(ability.get("bonus_ability"), display(ability.get("bonus_ability")))
    description = escape(display(ability.get("description"), ""))

    range_data = ability.get("range") or {}
    shape = RANGE_SHAPE_LABELS.get(range_data.get("shape"), display(range_data.get("shape")))
    distance = display(range_data.get("distance_m"))

    lines = [
        f"<b>• {name}</b>",
        f"Тип: {escape(str(ability_type))}",
        f"Ограничение: {escape(str(limit))}",
        f"Дальность: {escape(str(shape))}, {escape(str(distance))} м",
        f"Базовая характеристика: {escape(str(bonus_ability))}",
    ]

    damage = ability.get("damage")
    if damage:
        dice = display(damage.get("dice"))
        damage_type = DAMAGE_TYPE_LABELS.get(damage.get("type"), display(damage.get("type")))
        lines.append(f"Урон: {escape(str(dice))} ({escape(str(damage_type))})")

    control = ability.get("control")
    if control:
        control_type = CONTROL_TYPE_LABELS.get(control.get("type"), display(control.get("type")))
        duration = display(control.get("duration_rounds"))
        condition_end = escape(display(control.get("condition_end")))
        lines.append(f"Контроль: {escape(str(control_type))}, {escape(str(duration))} раунд.")
        lines.append(f"Снятие эффекта: {condition_end}")

    support = ability.get("support")
    if ability.get("type") == "support" and isinstance(support, dict) and support:
        support_type = SUPPORT_TYPE_LABELS.get(support.get("type"), display(support.get("type")))
        notes = escape(display(support.get("notes"), ""))
        lines.append(f"Поддержка: {escape(str(support_type))}")
        if notes:
            lines.append(f"Эффект: {notes}")

    if description:
        lines.append(f"Описание: {description}")

    return "\n".join(lines)


def format_character_message(data: dict) -> str:
    identity = data.get("identity", {})
    build = data.get("build", {})
    base_stats = data.get("base_stats", {})
    attrs = data.get("attributes_mods", {})
    abilities = data.get("abilities", [])
    backstory = data.get("backstory", {})

    name = escape(display(identity.get("name"), "-"))
    gender = GENDER_LABELS.get(identity.get("gender"), display(identity.get("gender")))
    age = display(identity.get("age"))

    race = escape(display(build.get("race")))
    char_class = escape(display(build.get("class")))
    subclass = build.get("subclass")
    background = build.get("background")
    alignment = build.get("alignment")
    level = display(build.get("level"))

    hp_base = display(base_stats.get("hp_base"))
    ac_base = display(base_stats.get("ac_base"))

    story = escape(display(backstory.get("story"), "—"))

    attrs_line = (
        f"СИЛ {display(attrs.get('str'))} | "
        f"ЛОВ {display(attrs.get('dex'))} | "
        f"ТЕЛ {display(attrs.get('con'))} | "
        f"ИНТ {display(attrs.get('int'))} | "
        f"МДР {display(attrs.get('wis'))} | "
        f"ХАР {display(attrs.get('cha'))}"
    )

    parts = [
        f"🧙 <b>{name}</b>",
        "",
        "<b>Основная информация</b>",
        f"Пол: {escape(str(gender))}",
        f"Возраст: {escape(str(age))}",
        f"Раса: {race}",
        f"Класс: {char_class}",
        f"Уровень: {escape(str(level))}",
    ]

    if subclass:
        parts.append(f"Подкласс: {escape(str(subclass))}")
    if background:
        parts.append(f"Предыстория: {escape(str(background))}")
    if alignment:
        parts.append(f"Мировоззрение: {escape(str(alignment))}")

    parts.extend([
        "",
        "<b>Базовые параметры</b>",
        f"HP: {escape(str(hp_base))}",
        f"AC: {escape(str(ac_base))}",
        "",
        "<b>Характеристики</b>",
        escape(attrs_line),
        "",
        "<b>Способности</b>",
    ])

    if abilities:
        for ability in abilities:
            parts.append(format_ability(ability))
            parts.append("")
    else:
        parts.append("Способности отсутствуют")
        parts.append("")

    parts.extend([
        "<b>История персонажа</b>",
        story,
    ])

    return "\n".join(parts).strip()
