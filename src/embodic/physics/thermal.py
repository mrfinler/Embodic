"""First-order temperature rise of a board or of a stack of boards (EQ-17)."""

from embodic.units import mm_to_m


def temperature_rise_k(loss_w: float, board_area_mm2: float, convection_h_w_m2k: float) -> float:
    """Return the steady temperature rise of a board or stack cooled by convection on both outer faces.

    References: EQ-17 (engine form), dT = P / (h 2 A). A stack of boards one gap apart cools through its two outer
    faces, so A is the face area of one board outline and P the loss of all boards (Xcoil massThermal, engine.js
    l.1390).

    Parameters
    ----------
    loss_w : float
        Total loss of the board, or of every board of the stack, in W.
    board_area_mm2 : float
        Face area of the stack in mm^2: one board outline, not the sum over boards.
    convection_h_w_m2k : float
        Convection coefficient in W/(m^2 K).

    Returns
    -------
    float
        Temperature rise in K.
    """
    return loss_w / (convection_h_w_m2k * 2.0 * mm_to_m(mm_to_m(board_area_mm2)))
