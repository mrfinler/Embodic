"""Interconnect roles for the mapped Xcoil layouts, from the items Xcoil's interconnectResistance reads.

The m1_layout fixtures keep each Xcoil interconnect item as one `ic` object without the tags that sort it
(engine.js l.1361-1372). The analysis fixtures carry those tags per item (`icItems`, written by
tools/golden/functions/physics.mjs), so an `ic` object is matched to its item by layer and first primitive. The role
follows Xcoil's precedence:

1. `line` set: LineLead of that line.
2. `tapOf` set: PhaseLink of the tap's phase (`N`) or of link k (`D<k>`).
3. `link` of net `D<k>`: PhaseLink of phase k.
4. `link` of net `N` (star ring): each stub with a tap becomes its own PhaseLink path, the rest is the NeutralRing.
5. anything else (the neutral pad lead): NeutralLead, counted in no sum.
"""

import dataclasses
from collections.abc import Mapping, Sequence
from typing import Any

from m1_layout.xcoil_map import PHASES, prim_from_record

from embodic.geometry.circuit import InterconnectRole, LineLead, NeutralLead, NeutralRing, PhaseLink
from embodic.geometry.layout import Layout
from embodic.geometry.paths import CopperPath

GEOMETRY_KEYS = ("x1", "y1", "x2", "y2", "cx", "cy", "r", "a1", "a2")


def _same_first_prim(record: Mapping[str, Any], first: Mapping[str, Any]) -> bool:
    return all(record.get(k) == first.get(k) for k in GEOMETRY_KEYS)


def _item_of(raw: Mapping[str, Any], layer_index: int, record: Mapping[str, Any], items: Sequence[Mapping[str, Any]]):
    found = [it for it in items if it["layer"] == layer_index and _same_first_prim(record, it["first"])]
    assert len(found) == 1, f"ic object on layer {layer_index} matches {len(found)} Xcoil items"
    return found[0]


def classify(layout: Layout, raw: Mapping[str, Any], items: Sequence[Mapping[str, Any]]) -> Layout:
    """Return the layout with one role per interconnect path; a star ring's tap stubs become their own paths."""
    paths = list(layout.paths)
    roles: list[InterconnectRole] = []
    ic_ids: list[int] = []
    objects = [(li, obj) for li, layer in enumerate(raw["layers"]) for obj in layer["objs"]]
    for path, (li, obj) in zip(layout.paths, objects, strict=True):
        if obj["kind"] != "ic":
            continue
        item = _item_of(raw, li, obj["prims"][0], items)
        if item["line"] is not None:
            roles.append(LineLead(path_id=path.id, phase=PHASES[item["line"]]))
        elif item["tapOf"] is not None:
            k = item["tapPhase"] if item["tapOf"] == "N" else int(item["tapOf"][1:])
            roles.append(PhaseLink(path_id=path.id, phase=PHASES[k]))
        elif item["linkNet"] is not None and item["linkNet"] != "N":
            roles.append(PhaseLink(path_id=path.id, phase=PHASES[int(item["linkNet"][1:])]))
        elif item["linkNet"] == "N":
            ring = []
            for record, kind, tap_phase in zip(obj["prims"], item["primKinds"], item["primTapPhase"], strict=True):
                if kind == "stub" and tap_phase is not None:
                    stub = _stub_path(path, len(paths), record)
                    paths.append(stub)
                    roles.append(PhaseLink(path_id=stub.id, phase=PHASES[tap_phase]))
                    ic_ids.append(stub.id)
                else:
                    ring.append(prim_from_record(record))
            paths[path.id] = dataclasses.replace(path, primitives=tuple(ring))
            roles.append(NeutralRing(path_id=path.id, tap_via_ids=tuple(item["ringTapVias"])))
        else:
            roles.append(NeutralLead(path_id=path.id))
        ic_ids.append(path.id)
    circuit = dataclasses.replace(layout.circuit, interconnect_path_ids=tuple(ic_ids), interconnect_roles=tuple(roles))
    return dataclasses.replace(layout, paths=tuple(paths), circuit=circuit)


def _stub_path(ring: CopperPath, path_id: int, record: Mapping[str, Any]) -> CopperPath:
    return dataclasses.replace(ring, id=path_id, primitives=(prim_from_record(record),))
