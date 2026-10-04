"""Optional user overrides of registry material constants (interfaces.md section 2.1)."""

from dataclasses import dataclass

from embodic.units import Unit


@dataclass(frozen=True, slots=True, kw_only=True)
class PropertyValue:
    """A user override of a registry constant. Without an override the registry constant and its EV status apply."""

    value: float
    unit: Unit


@dataclass(frozen=True, slots=True, kw_only=True)
class MaterialOverrides:
    """Each None keeps the registry constant."""

    copper_resistivity_20c_ohm_m: PropertyValue | None = None
    copper_temp_coeff_per_k: PropertyValue | None = None
    copper_density_g_per_cm3: PropertyValue | None = None
    laminate_density_g_per_cm3: PropertyValue | None = None
