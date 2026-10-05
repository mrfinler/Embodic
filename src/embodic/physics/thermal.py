"""First-order temperature rise of the board (EQ-17)."""

from embodic.units import mm_to_m


def temperature_rise_k(loss_w: float, board_area_mm2: float, convection_h_w_m2k: float) -> float:
    """Return the steady temperature rise of a board cooled by convection on both faces.

    References: EQ-17 (engine form), dT = P / (h 2 A).

    Parameters
    ----------
    loss_w : float
        Total loss in W.
    board_area_mm2 : float
        Area of one board face in mm^2.
    convection_h_w_m2k : float
        Convection coefficient in W/(m^2 K).

    Returns
    -------
    float
        Temperature rise in K.
    """
    return loss_w / (convection_h_w_m2k * 2.0 * mm_to_m(mm_to_m(board_area_mm2)))
