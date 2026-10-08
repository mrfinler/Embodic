"""Circuit.interconnect_roles consistency with interconnect_path_ids (interfaces.md section 5, U-M2e-4)."""

import pytest

from embodic.geometry.circuit import Circuit, LineLead, NeutralLead, NeutralRing, PhaseLink
from embodic.model.vocabulary import ConnectionTopology, Phase

ROLES = (
    LineLead(path_id=10, phase=Phase.A),
    PhaseLink(path_id=11, phase=Phase.B),
    NeutralRing(path_id=12, tap_via_ids=(0, 1, 2)),
    NeutralLead(path_id=13),
)


def _circuit(ids: tuple[int, ...], roles: tuple[object, ...]) -> Circuit:
    return Circuit(
        phases=(),
        topology=ConnectionTopology.STAR,
        interconnect_path_ids=ids,
        interconnect_roles=roles,  # type: ignore[arg-type]
    )


def test_one_role_per_interconnect_path_is_accepted() -> None:
    """Defect caught: a valid classification rejected, so no generator could record roles."""
    circuit = _circuit((13, 12, 11, 10), ROLES)
    assert {role.kind for role in circuit.interconnect_roles} == {
        "line_lead",
        "phase_link",
        "neutral_ring",
        "neutral_lead",
    }


def test_no_roles_means_unclassified_and_is_accepted() -> None:
    """Defect caught: hand-built layouts and the Xcoil mapper fail to construct without roles."""
    circuit = Circuit(phases=(), topology=ConnectionTopology.STAR, interconnect_path_ids=(1, 2))
    assert circuit.interconnect_roles == ()


@pytest.mark.parametrize(
    ("ids", "roles"),
    [
        ((10, 11, 12), ROLES),  # a role for a path that is not interconnect copper
        ((10, 11, 12, 13, 14), ROLES),  # an interconnect path without a role
        ((10, 11, 12, 13), (*ROLES[:3], LineLead(path_id=10, phase=Phase.C))),  # one path classified twice
    ],
)
def test_roles_that_do_not_match_the_interconnect_ids_are_rejected(
    ids: tuple[int, ...], roles: tuple[object, ...]
) -> None:
    """Defect caught: a path counted twice or missed in P_ic because the role list drifted from the path list."""
    with pytest.raises(ValueError, match="exactly once"):
        _circuit(ids, roles)
