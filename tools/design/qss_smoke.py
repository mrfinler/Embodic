"""Load ``light.qss`` and ``dark.qss`` in real Qt, offscreen, and prove the hooks apply by sampling pixels.

Usage, from the repository root::

    QT_QPA_PLATFORM=offscreen python tools/design/qss_smoke.py [--out docs/phase2/design]

Builds one widget of every styled kind, saves ``theme_smoke_<theme>.png`` into ``--out``, and compares four sampled
pixels per theme with their tokens (result-card border and fill, primary button fill, invalid-field border). Exit
code 1 when a pixel differs or Qt prints a message other than the offscreen plugin's propagateSizeHints notice.
"""

import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QByteArray, QDir, QPoint, QSize, Qt, qInstallMessageHandler
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap, QStandardItem, QStandardItemModel
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTableView,
    QTabWidget,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "resources"
TOKENS = json.loads((RES / "themes" / "tokens.json").read_text(encoding="utf-8"))
BENIGN = "This plugin does not support propagateSizeHints()"
SECTIONS = (
    ("File", ("new", "open", "save")),
    ("Topology", ("topology-spiral", "topology-serpentine", "topology-wave")),
    ("View", ("zoom-fit", "labels", "theme")),
    ("Analysis", ("compute", "drc", "export-pdf")),
)


def icon(name: str, theme: str, size: int = 24) -> QIcon:
    """Return the icon recoloured per QIcon mode, as design_spec.md section 7 tells the loader to."""
    ic = QIcon()
    for mode, key in ((QIcon.Mode.Normal, "normal"), (QIcon.Mode.Disabled, "disabled")):
        text = (RES / "icons" / f"{name}.svg").read_text(encoding="utf-8")
        text = text.replace("currentColor", TOKENS["themes"][theme]["icon_color"][key])
        if size <= 16:
            text = text.replace('stroke-width="1.5"', 'stroke-width="2"')
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        QSvgRenderer(QByteArray(text.encode())).render(p)
        p.end()
        ic.addPixmap(pm, mode)
    return ic


def prop(w: QWidget, **kv: object) -> QWidget:
    """Set dynamic properties (the QSS hooks) and return the widget."""
    for k, v in kv.items():
        w.setProperty(k, v)
    return w


def toolstrip(theme: str) -> QToolBar:
    """Return a toolstrip with four sections; the first Topology button is checked, the last Analysis disabled."""
    tb = QToolBar()
    tb.setObjectName("toolstrip")
    tb.setMovable(False)
    for title, names in SECTIONS:
        sec = prop(QFrame(), **{"class": "ts-section"})
        v = QVBoxLayout(sec)
        v.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        for i, n in enumerate(names):
            b = prop(QToolButton(), **{"class": "ts-large"})
            b.setIcon(icon(n, theme))
            b.setIconSize(QSize(24, 24))
            b.setText(n.split("-")[-1].title())
            b.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            b.setCheckable(True)
            b.setChecked(title == "Topology" and i == 0)
            b.setEnabled(not (title == "Analysis" and i == 2))
            row.addWidget(b)
        v.addLayout(row)
        v.addWidget(prop(QLabel(title), **{"class": "ts-caption"}), 0, Qt.AlignmentFlag.AlignHCenter)
        tb.addWidget(sec)
    return tb


def inspector(theme: str) -> tuple[QWidget, QPushButton, QLineEdit]:
    """Return the inspector pane with every form control kind, the primary button and an invalid field."""
    insp = QWidget()
    insp.setObjectName("inspector")
    insp.setFixedWidth(340)
    iv = QVBoxLayout(insp)
    tabs = QTabWidget()
    for name, label in (("topology-spiral", "Coil"), ("phases", "Phases"), ("layers", "Layers")):
        tabs.addTab(QWidget(), icon(name, theme, 16), label)
    iv.addWidget(tabs)
    gb = QGroupBox("Turns and copper")
    f = QFormLayout(gb)
    f.addRow("Turns per coil", QLineEdit("7"))
    bad = prop(QLineEdit("0.05"), invalid=True)
    bad.setObjectName("param-clearance")
    f.addRow("Trace spacing", bad)
    f.addRow("", prop(QLabel("Must be at least 0.10 mm (board limit)."), **{"class": "field-error"}))
    sp = QDoubleSpinBox()
    sp.setValue(0.2)
    f.addRow("Trace width", sp)
    cb = QComboBox()
    cb.addItems(["Arc", "Straight", "Stadium"])
    f.addRow("End style", cb)
    chk = QCheckBox("Rotate alternate layer groups")
    chk.setChecked(True)
    f.addRow(chk)
    dis = QLineEdit("12")
    dis.setEnabled(False)
    f.addRow("Disabled", dis)
    ro = QLineEdit("24")
    ro.setReadOnly(True)
    f.addRow("Derived", ro)
    iv.addWidget(gb)
    chips = QHBoxLayout()
    for pv in ("user", "example", "default", "measured"):
        chips.addWidget(prop(QLabel(pv), **{"class": "prov-chip", "provenance": pv}))
    iv.addLayout(chips)
    nb = QHBoxLayout()
    nb.addWidget(QPushButton("Cancel"))
    pb = prop(QPushButton("Create design"), **{"class": "primary"})
    nb.addWidget(pb)
    iv.addLayout(nb)
    iv.addStretch(1)
    return insp, pb, bad


def canvas() -> QWidget:
    """Return the centre pane with a layer table."""
    mid = QWidget()
    mid.setObjectName("fig-canvas")
    mv = QVBoxLayout(mid)
    t = QTableView()
    m = QStandardItemModel(4, 3)
    m.setHorizontalHeaderLabels(["Layer", "Group", "Rotation"])
    for r in range(4):
        for c, val in enumerate((f"L{r + 1}", "X" if r % 2 == 0 else "Y", f"{15 * (r // 2)} deg")):
            m.setItem(r, c, QStandardItem(val))
    t.setModel(m)
    t.setAlternatingRowColors(True)
    mv.addWidget(t)
    return mid


def rail() -> tuple[QWidget, QFrame]:
    """Return the results rail with one result card (every badge, chip and check state) and a notice."""
    pane = QWidget()
    pane.setObjectName("results-rail")
    pane.setFixedWidth(360)
    rv = QVBoxLayout(pane)
    card = prop(QFrame(), **{"class": "result-card"})
    card.setObjectName("res-card-r-phase")
    cv = QVBoxLayout(card)
    cv.addWidget(QLabel("Phase resistance R_ph"))
    vr = QHBoxLayout()
    val = prop(QLabel("1.07"), **{"class": "result-value"})
    val.setObjectName("res-r-phase-value")
    vr.addWidget(val)
    vr.addWidget(prop(QLabel("ohm"), **{"class": "result-unit"}))
    vr.addStretch(1)
    cv.addLayout(vr)
    meta = QHBoxLayout()
    for st in ("verified", "inferred", "assumption", "unresolved", "not-tested"):
        meta.addWidget(prop(QLabel(st.replace("-", " ")), **{"class": "badge", "status": st}))
    cv.addLayout(meta)
    m2 = QHBoxLayout()
    m2.addWidget(prop(QLabel("EQ-10"), **{"class": "eq-chip"}))
    tag = prop(QToolButton(), **{"class": "asm-tag"})
    tag.setText("3 assumptions")
    m2.addWidget(tag)
    for s in ("pass", "fail", "warn"):
        m2.addWidget(prop(QLabel(s.title()), **{"class": "check-state", "state": s}))
    m2.addStretch(1)
    cv.addLayout(m2)
    rv.addWidget(card)
    note = prop(QFrame(), **{"class": "notice"})
    QVBoxLayout(note).addWidget(QLabel("Changed from 8 to 7: coil count must divide by 3."))
    rv.addWidget(note)
    rv.addStretch(1)
    return pane, card


def check_theme(theme: str, out: Path, app: QApplication, messages: list[str]) -> list[str]:
    """Render one theme, save its PNG and return the failures (empty when every sample matches)."""
    messages.clear()
    app.setStyleSheet((RES / "themes" / f"{theme}.qss").read_text(encoding="utf-8"))
    win = QMainWindow()
    win.resize(1100, 640)
    win.addToolBar(toolstrip(theme))
    central = QWidget()
    h = QHBoxLayout(central)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(0)
    insp, pb, bad = inspector(theme)
    pane, card = rail()
    h.addWidget(insp)
    h.addWidget(canvas(), 1)
    h.addWidget(pane)
    win.setCentralWidget(central)
    win.statusBar().addWidget(QLabel("Ready. DRC: 1 failure"))
    win.show()
    app.processEvents()
    img: QImage = win.grab().toImage()
    img.save(str(out / f"theme_smoke_{theme}.png"))

    def px(w: QWidget, x: int, y: int) -> str:
        return img.pixelColor(w.mapTo(win, QPoint(x, y))).name()

    c = TOKENS["themes"][theme]["color"]
    samples = {
        "result-card border": (px(card, 0, card.height() // 2), c["divider"]),
        "result-card fill": (px(card, 4, card.height() - 4), c["surface"]),
        "primary button fill": (px(pb, pb.width() // 2, 3), c["surface-inverse"]),
        "invalid field border": (px(bad, 0, bad.height() // 2), c["status-fail"]),
    }
    win.close()
    failures = [f"{theme}: {k} is {got}, token {want}" for k, (got, want) in samples.items() if got != want]
    failures += [f"{theme}: Qt message: {m}" for m in messages if BENIGN not in m]
    for k, (got, want) in samples.items():
        print(f"{theme:5} {k:22} sampled {got} token {want} {'ok' if got == want else 'MISMATCH'}")
    return failures


def main() -> int:
    """Run both themes; return 1 on any failure."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=REPO / "docs" / "phase2" / "design")
    out = parser.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    messages: list[str] = []
    qInstallMessageHandler(lambda _mode, _ctx, msg: messages.append(msg))
    app = QApplication(sys.argv)
    QDir.addSearchPath("theme", str(RES / "themes"))
    failures = check_theme("light", out, app, messages) + check_theme("dark", out, app, messages)
    for f in failures:
        print("FAIL", f)
    print(f"qss_smoke: {'FAIL' if failures else 'pass'} ({len(failures)} failures)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
