from __future__ import annotations

from typing import TypedDict, TypeAlias, Any, cast, NotRequired


ConfigValue: TypeAlias = str | int | float | list["ConfigValue"]


class ConfigError(Exception):
    def __str__(self) -> str:
        return f"Config - {super().__str__()}"


class ConfigElement(TypedDict):
    type: str
    name: str


class ConfigClass(ConfigElement):
    parent: NotRequired[str]
    members: NotRequired[list[ConfigElement]]


class ConfigProperty(ConfigElement):
    value: ConfigValue
    extends: NotRequired[bool]


def validate_config_value_type(value: Any) -> None:
    if not isinstance(value, (str, int, float, list)):
        raise TypeError(
            f"{type(value)} is not a valid type for config value"
        )

    if not isinstance(value, list) or len(value) == 0:
        return

    for item in value:
        validate_config_value_type(item)


def validate_config_property_type(element: ConfigElement) -> None:
    value = element.get("value")
    if value is None:
        raise ConfigError(
            "value is missing from property or is None"
        )

    validate_config_value_type(value)

    if not isinstance(value, list) and element.get("extends", False):
        raise ConfigError(
            "property extension is only supported on arrays"
        )


def validate_config_class_type(element: ConfigElement) -> None:
    parent = element.get("parent")
    if (
        parent is not None
        and not (isinstance(parent, str) and parent != "")
    ):
        raise ConfigError(
            f"invalid class parent: {parent}"
        )

    members = element.get("members")
    if (
        members is not None
        and not isinstance(members, list)
    ):
        raise TypeError(
            f"{type(element)} is not a valid type for class members"
        )

    if members is None:
        return

    for member in members:
        validate_config_element_type(member)


def validate_config_element_type(element: Any) -> None:
    if not isinstance(element, dict):
        raise TypeError(
            f"{type(element)} is not a valid type for config element"
        )

    elemtype = element.get("type")
    if elemtype not in ("class", "property", "delete", "external"):
        raise ConfigError(
            f"invalid config element type: {elemtype}"
        )

    name = element.get("name")
    if (
        not isinstance(name, str)
        or name == ""
    ):
        raise ConfigError(
            f"invalid config element name: {name}"
        )

    element = cast(ConfigElement, element)

    match elemtype:
        case "class":
            validate_config_class_type(element)
        case "property":
            validate_config_property_type(element)


def validate_config_types(data: Any) -> None:
    if not isinstance(data, list):
        raise TypeError(
            f"{type(data)} is not a valid type for config root object"
        )

    for item in data:
        validate_config_element_type(item)


def _indent(text: str, level: int = 0) -> str:
    return "\t" * level + text


def format_config_value(value: ConfigValue, indent: int = 0) -> str:
    match value:
        case str():
            return f"\"{value}\""
        case int():
            return f"{value:d}"
        case float():
            return f"{value:f}"

    if len(value) == 0:
        return "{}"

    items = [
        _indent(
            format_config_value(v, indent + 1),
            indent + 1
        ) for v in value]

    value = f"{{\n{',\n'.join(items)}\n{_indent('}', indent)}"

    return value


def format_config_property(data: ConfigProperty, indent: int = 0) -> str:
    name = _indent(data["name"], indent)
    if isinstance(data["value"], list):
        name += "[]"

    value = format_config_value(data["value"], indent)

    op = "+=" if data.get("extends") else "="

    return (
        f"{name} {op} {value};\n"
    )


def format_config_class(data: ConfigClass, indent: int = 0) -> str:
    value = ""

    if data.get("parent") is not None:
        value += _indent(
            f"class {data["name"]}: {data["parent"]} {{",
            indent
        )
    else:
        value += _indent(f"class {data["name"]} {{", indent)

    members = data.get("members")
    if members is None or len(members) == 0:
        return value + "};\n"

    value += "\n"

    for item in members:
        value += format_config_element(item, indent + 1)

    value += _indent("};\n", indent)
    return value


def format_config_element(data: ConfigElement, indent: int = 0) -> str:
    value = ""
    match data["type"]:
        case "class":
            value += format_config_class(
                cast(ConfigClass, data),
                indent
            )
        case "property":
            value += format_config_property(
                cast(ConfigProperty, data),
                indent
            )
        case "delete":
            value += _indent(f"del {data['name']};\n", indent)
        case "external":
            value += _indent(f"class {data['name']};\n", indent)
        case _:
            raise ValueError(
                f"invalid config element type: {data['type']}"
            )

    return value


def format_config(data: list[ConfigElement]) -> str:
    value = ""

    for item in data:
        value += format_config_element(item)

    return value
