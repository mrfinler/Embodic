"""The shape of DesignParameters read from its type hints: JSON conversion, JSON pointers and input leaves.

One walk over the dataclass annotations gives every input leaf of a topology, so the field table, the draft and the
provenance map all describe the same pointers as the dataclasses (ADR-0010 decision 2).
"""

import dataclasses
import functools
import types
import typing
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal, TypeAlias

from embodic.model.design import DesignParameters
from embodic.model.vocabulary import TopologyKind
from embodic.model.winding_specs import SerpentineWindingSpec, SpiralWindingSpec, WaveWindingSpec, WindingSpec

JsonValue: TypeAlias = "bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None"
Choice: TypeAlias = str | int

WINDING_BY_TOPOLOGY: Mapping[TopologyKind, type[WindingSpec]] = types.MappingProxyType(
    {
        TopologyKind.SPIRAL: SpiralWindingSpec,
        TopologyKind.SERPENTINE: SerpentineWindingSpec,
        TopologyKind.WAVE: WaveWindingSpec,
    }
)
LIST_ITEM = "*"


class ValueType(StrEnum):
    """What a leaf holds. GROUP and LIST leaves exist only while their container is absent (None) or empty ([])."""

    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    TEXT = "text"
    CHOICE = "choice"
    INT_LIST = "int_list"
    INT_GROUPS = "int_groups"
    CHOICE_LIST = "choice_list"
    GROUP = "group"
    LIST = "list"


@dataclass(frozen=True, slots=True, kw_only=True)
class Leaf:
    """One input leaf of the design for one topology, derived from the annotations."""

    pattern: str
    value_type: ValueType
    choices: tuple[Choice, ...]
    nullable: bool
    required: bool
    neutral_value: JsonValue
    topologies: frozenset[TopologyKind]
    variant: Choice | None = None  # tag value of the union member that owns the leaf; None if every member has it


@dataclass(frozen=True, slots=True)
class _Variant:
    tag: str
    classes: Mapping[Choice, type]
    nullable: bool


@dataclass(frozen=True, slots=True)
class _ListOf:
    item: "type | _Variant"
    nullable: bool


@functools.cache
def _hints(cls: type) -> Mapping[str, Any]:
    """Return the resolved annotations of a class; evaluating them costs the same on every call, so do it once."""
    return types.MappingProxyType(typing.get_type_hints(cls))


def _non_none(tp: Any) -> tuple[tuple[Any, ...], bool]:
    """Split an annotation into its non-None members and whether None is allowed."""
    if typing.get_origin(tp) in (types.UnionType, typing.Union):
        members = typing.get_args(tp)
        return tuple(m for m in members if m is not type(None)), type(None) in members
    return (tp,), False


def _tag_field(cls: type) -> tuple[str, Choice] | None:
    """Return the discriminator of a union member: the field typed as a one-value Literal with that default."""
    for f in dataclasses.fields(cls):
        hint = _hints(cls)[f.name]
        if typing.get_origin(hint) is Literal and len(typing.get_args(hint)) == 1 and f.name in ("kind", "shape"):
            return f.name, typing.get_args(hint)[0]
    return None


def _container(tp: Any) -> "type | _Variant | _ListOf | None":
    """Classify an annotation as a record, a tagged union of records, a list of either, or None for a scalar."""
    members, nullable = _non_none(tp)
    if len(members) == 1 and typing.get_origin(members[0]) is tuple:
        item_tp = typing.get_args(members[0])[0]
        item = _container(item_tp)
        if isinstance(item, type | _Variant):
            return _ListOf(item, nullable)
        return None
    if all(dataclasses.is_dataclass(m) for m in members):
        if len(members) == 1:
            single = typing.cast(type, members[0])
            return _Variant(tag="", classes={"": single}, nullable=True) if nullable else single
        tags = [_tag_field(m) for m in members]
        if any(t is None for t in tags):
            raise TypeError(f"union {tp} has a member without a kind or shape tag")
        tag_names = {t[0] for t in tags if t is not None}
        if len(tag_names) != 1:
            raise TypeError(f"union {tp} mixes tag fields {tag_names}")
        return _Variant(tag_names.pop(), {t[1]: m for t, m in zip(tags, members, strict=True) if t}, nullable)
    return None


def _scalar(tp: Any) -> tuple[ValueType, tuple[Choice, ...], bool]:
    """Classify a scalar annotation; raises TypeError for an annotation the model does not use."""
    members, nullable = _non_none(tp)
    if len(members) != 1:
        raise TypeError(f"unsupported scalar annotation {tp}")
    base = members[0]
    origin = typing.get_origin(base)
    if origin is Literal:
        return ValueType.CHOICE, typing.get_args(base), nullable
    if origin is tuple:
        item = typing.get_args(base)[0]
        if item is int:
            return ValueType.INT_LIST, (), nullable
        if typing.get_origin(item) is tuple:
            return ValueType.INT_GROUPS, (), nullable
        if isinstance(item, type) and issubclass(item, StrEnum):
            return ValueType.CHOICE_LIST, tuple(m.value for m in item), nullable
    if isinstance(base, type) and issubclass(base, StrEnum):
        return ValueType.CHOICE, tuple(m.value for m in base), nullable
    simple = {bool: ValueType.BOOL, int: ValueType.INT, float: ValueType.FLOAT, str: ValueType.TEXT}
    if base in simple:
        return simple[base], (), nullable
    raise TypeError(f"unsupported scalar annotation {tp}")


def is_constant(cls: type, f: dataclasses.Field[Any]) -> bool:
    """Return True for a field that is not an input: a one-value Literal with that value as default."""
    hint = _hints(cls)[f.name]
    return typing.get_origin(hint) is Literal and len(typing.get_args(hint)) == 1


def _default(f: dataclasses.Field[Any]) -> tuple[bool, Any]:
    """Return (has_default, default value) of a dataclass field."""
    if f.default is not dataclasses.MISSING:
        return True, f.default
    if f.default_factory is not dataclasses.MISSING:
        return True, f.default_factory()
    return False, None


def _field_type(cls: type, name: str, topology: TopologyKind) -> Any:
    """Annotation of a field, with the winding union narrowed to the topology's spec."""
    if cls is DesignParameters and name == "winding":
        return WINDING_BY_TOPOLOGY[topology]
    return _hints(cls)[name]


def _record_leaves(cls: type, pointer: str, topology: TopologyKind) -> Iterator[Leaf]:
    for f in dataclasses.fields(cls):
        if is_constant(cls, f):
            continue
        has_default, default = _default(f)
        yield from _leaves_of(_field_type(cls, f.name, topology), f"{pointer}/{f.name}", has_default, default, topology)


def _leaves_of(tp: Any, pointer: str, has_default: bool, default: Any, topology: TopologyKind) -> Iterator[Leaf]:
    shape = _container(tp)
    every = frozenset({topology})
    if shape is None:
        value_type, choices, nullable = _scalar(tp)
        neutral = to_json(default) if has_default else None
        yield Leaf(
            pattern=pointer,
            value_type=value_type,
            choices=choices,
            nullable=nullable,
            required=not has_default,
            neutral_value=neutral,
            topologies=every,
        )
        return
    if isinstance(shape, type):
        yield from _record_leaves(shape, pointer, topology)
        return
    if isinstance(shape, _ListOf):
        neutral = to_json(default) if has_default else None
        yield Leaf(
            pattern=pointer,
            value_type=ValueType.LIST,
            choices=(),
            nullable=shape.nullable,
            required=not has_default,
            neutral_value=neutral,
            topologies=every,
        )
        yield from _leaves_of_item(shape.item, f"{pointer}/{LIST_ITEM}", topology)
        return
    if shape.nullable:
        yield Leaf(
            pattern=pointer,
            value_type=ValueType.GROUP,
            choices=(),
            nullable=True,
            required=not has_default,
            neutral_value=to_json(default) if has_default else None,
            topologies=every,
        )
    yield from _leaves_of_item(shape, pointer, topology)


def _leaves_of_item(item: "type | _Variant", pointer: str, topology: TopologyKind) -> Iterator[Leaf]:
    if isinstance(item, type):
        yield from _record_leaves(item, pointer, topology)
        return
    if item.tag:
        yield Leaf(
            pattern=f"{pointer}/{item.tag}",
            value_type=ValueType.CHOICE,
            choices=tuple(item.classes),
            nullable=False,
            required=True,
            neutral_value=None,
            topologies=frozenset({topology}),
        )
    for tag, cls in item.classes.items():
        for leaf in _record_leaves(cls, pointer, topology):
            yield dataclasses.replace(leaf, variant=tag) if item.tag and leaf.variant is None else leaf


@functools.cache
def leaves(topology: TopologyKind) -> tuple[Leaf, ...]:
    """Return every input leaf of a topology's design in dataclass field order (patterns use '*' for list items)."""
    return tuple(_record_leaves(DesignParameters, "", topology))


def to_json(value: Any) -> JsonValue:
    """Convert a model value to plain JSON data: records to dicts, tuples to lists, enums to their values."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_json(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, tuple):
        return [to_json(v) for v in value]
    if isinstance(value, StrEnum):
        return value.value
    return typing.cast(JsonValue, value)


def from_json(tp: Any, data: Any) -> Any:
    """Build a model value of annotation `tp` from JSON data whose leaves were already checked (parse_draft).

    Raises
    ------
    KeyError, TypeError, ValueError
        On data that does not have the shape of `tp`, which is a programming error once leaves are checked.
    """
    members, nullable = _non_none(tp)
    if data is None and nullable:
        return None
    shape = _container(tp)
    if shape is None:
        return _scalar_from_json(members[0], data)
    if isinstance(shape, _ListOf):
        return tuple(_item_from_json(shape.item, d) for d in data)
    return _item_from_json(shape, data)


def _item_from_json(item: "type | _Variant", data: Mapping[str, Any]) -> Any:
    cls = item if isinstance(item, type) else item.classes[data[item.tag] if item.tag else ""]
    hints = _hints(cls)
    kwargs = {f.name: from_json(hints[f.name], data[f.name]) for f in dataclasses.fields(cls) if f.name in data}
    return cls(**kwargs)


def _scalar_from_json(base: Any, data: Any) -> Any:
    origin = typing.get_origin(base)
    if origin is tuple:
        item = typing.get_args(base)[0]
        return tuple(_scalar_from_json(item, d) for d in data)
    if isinstance(base, type) and issubclass(base, StrEnum):
        return base(data)
    if base is float:
        return float(data)
    return data


def design_from_json(topology: TopologyKind, data: Mapping[str, Any]) -> DesignParameters:
    """Build a design from checked JSON data; the winding variant comes from `topology`."""
    winding = from_json(WINDING_BY_TOPOLOGY[topology], data["winding"])
    hints = _hints(DesignParameters)
    kwargs = {
        f.name: winding if f.name == "winding" else from_json(hints[f.name], data[f.name])
        for f in dataclasses.fields(DesignParameters)
        if f.name in data
    }
    return DesignParameters(**kwargs)


def flatten(data: JsonValue, pointer: str = "") -> dict[str, JsonValue]:
    """Map every leaf of JSON data to its JSON pointer; an empty list of records or a None stays a leaf."""
    if isinstance(data, dict):
        out: dict[str, JsonValue] = {}
        for key, child in data.items():
            out.update(flatten(child, f"{pointer}/{key}"))
        return out
    if isinstance(data, list) and data and all(isinstance(item, dict) for item in data):
        out = {}
        for index, child in enumerate(data):
            out.update(flatten(child, f"{pointer}/{index}"))
        return out
    return {pointer: data}


def unflatten(values: Mapping[str, JsonValue]) -> dict[str, Any]:
    """Inverse of flatten: rebuild nested JSON data; all-digit pointer segments become list indices."""
    root: dict[str, Any] = {}
    for pointer, value in values.items():
        node = root
        segments = pointer.split("/")[1:]
        for segment in segments[:-1]:
            child = node.get(segment)
            if not isinstance(child, dict):
                child = node[segment] = {}
            node = child
        if not (isinstance(node.get(segments[-1]), dict) and value in (None, [])):
            node[segments[-1]] = value
    return typing.cast(dict[str, Any], _lists(root))


def _lists(node: Any) -> Any:
    if not isinstance(node, dict):
        return node
    converted = {key: _lists(child) for key, child in node.items()}
    if converted and all(key.isdigit() for key in converted):
        return [converted[str(index)] for index in range(len(converted))]
    return converted


def field_key(pattern: str, variant: Choice | None) -> str:
    """Key of a field in the table: the pattern, plus '#<tag>' for a leaf owned by one union member."""
    return pattern if variant is None else f"{pattern}#{variant}"


def pattern_of(pointer: str) -> str:
    """Replace list indices in a concrete pointer with '*' ("/stackup/layers/0/name" -> "/stackup/layers/*/name")."""
    return "/".join(LIST_ITEM if segment.isdigit() else segment for segment in pointer.split("/"))


def design_values(design: DesignParameters) -> dict[str, JsonValue]:
    """Return every input leaf of a design by concrete pointer, without the constant fields."""
    data = typing.cast(dict[str, JsonValue], to_json(design))
    allowed = {leaf.pattern for leaf in leaves(design.topology)}
    return {pointer: value for pointer, value in flatten(data).items() if pattern_of(pointer) in allowed}


@dataclass(frozen=True, slots=True, kw_only=True)
class Resolution:
    """Which pointers of a draft apply to its structure, and which required ones have no value."""

    active: tuple[str, ...]  # present pointers that belong to the chosen variants and list items
    missing: tuple[str, ...]  # required pointers without a value
    malformed: tuple[str, ...]  # list pointers whose item indices are not 0..n-1


def resolve(topology: TopologyKind, values: Mapping[str, JsonValue]) -> Resolution:
    """Walk the design structure over a pointer map; absent optional fields fall back to their defaults."""
    walk = _DraftWalk(topology, values)
    walk.record(DesignParameters, "")
    return Resolution(active=tuple(walk.active), missing=tuple(walk.missing), malformed=tuple(walk.malformed))


class _DraftWalk:
    def __init__(self, topology: TopologyKind, values: Mapping[str, JsonValue]) -> None:
        self.topology = topology
        self.values = values
        self.active: list[str] = []
        self.missing: list[str] = []
        self.malformed: list[str] = []

    def present_under(self, pointer: str) -> bool:
        prefix = pointer + "/"
        return pointer in self.values or any(key.startswith(prefix) for key in self.values)

    def record(self, cls: type, pointer: str) -> None:
        for f in dataclasses.fields(cls):
            if is_constant(cls, f):
                continue
            child = f"{pointer}/{f.name}"
            has_default, _ = _default(f)
            if has_default and not self.present_under(child):
                continue
            self.node(_field_type(cls, f.name, self.topology), child)

    def node(self, tp: Any, pointer: str) -> None:
        shape = _container(tp)
        if shape is None:
            (self.active if pointer in self.values else self.missing).append(pointer)
        elif isinstance(shape, type):
            self.record(shape, pointer)
        elif isinstance(shape, _ListOf):
            self.items(shape, pointer)
        elif shape.nullable and pointer in self.values:
            self.active.append(pointer)
        else:
            self.item(shape, pointer)

    def items(self, shape: _ListOf, pointer: str) -> None:
        if pointer in self.values:
            self.active.append(pointer)
            return
        prefix = pointer + "/"
        segments = {key[len(prefix) :].split("/")[0] for key in self.values if key.startswith(prefix)}
        indices = sorted(int(segment) for segment in segments if segment.isdigit())
        if not segments:
            self.missing.append(pointer)
            return
        if indices != list(range(len(segments))):
            self.malformed.append(pointer)
        for index in indices:
            self.item(shape.item, f"{pointer}/{index}")

    def item(self, item: "type | _Variant", pointer: str) -> None:
        if isinstance(item, type):
            self.record(item, pointer)
            return
        if not item.tag:
            self.record(item.classes[""], pointer)
            return
        tag_pointer = f"{pointer}/{item.tag}"
        if tag_pointer not in self.values:
            self.missing.append(tag_pointer)
            return
        self.active.append(tag_pointer)
        tag = self.values[tag_pointer]
        if isinstance(tag, str | int) and not isinstance(tag, bool) and tag in item.classes:
            self.record(item.classes[tag], pointer)
