"""Print the accessible text of the unit-bearing table cells of the inspector (DEF-UV13-02, REQ-N-24, U-V13).

    QT_QPA_PLATFORM=offscreen PYTHONPATH=src python3 tests/independent/m7/n24_table_cells.py

For `layer-list` and `screw-table` of two spiral examples: the column headers, and for each cell of row 0 its display
text, AccessibleTextRole, AccessibleDescriptionRole and any index widget's accessible description. A cell that holds a
number and has neither role set leaves its unit to the column header alone.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m4"))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView
from ui_driver import close, load_example, open_window

TABLES = ("layer-list", "screw-table")
EXAMPLES = ("spiral_12c10p_d08", "spiral_12c16p_default")


def main() -> int:
    """Print one block per example and table."""
    with tempfile.TemporaryDirectory() as folder:
        window = open_window(Path(folder))
        for example in EXAMPLES:
            load_example(window, example)
            for name in TABLES:
                view = window.findChild(QAbstractItemView, name)
                model = view.model()
                headers = [model.headerData(c, Qt.Orientation.Horizontal) for c in range(model.columnCount())]
                print(f"{example} {name} {model.rowCount()}x{model.columnCount()} headers {headers}")
                for column in range(model.columnCount() if model.rowCount() else 0):
                    index = model.index(0, column)
                    widget = view.indexWidget(index)
                    print(
                        f"  (0,{column}) display={model.data(index)!r} "
                        f"text={model.data(index, Qt.ItemDataRole.AccessibleTextRole)!r} "
                        f"description={model.data(index, Qt.ItemDataRole.AccessibleDescriptionRole)!r} "
                        f"widget={widget.accessibleDescription() if widget else None!r}"
                    )
        close(window)
    return 0


if __name__ == "__main__":
    sys.exit(main())
