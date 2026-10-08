"""Build evidence_register.json from the Phase 1 register and the Phase 2 added rows.

Rerun from the repository root: python3 docs/phase2/evidence/tools/build_evidence_register.py
The script refuses to write when a row falls outside a mapping rule, so every label in the JSON is traceable to a rule.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PHASE1_MD = ROOT / "docs/phase1/evidence/evidence_register.md"
PHASE2_MD = ROOT / "docs/phase2/evidence/evidence_register.md"
EQ_REGISTRY = ROOT / "docs/phase1/engineering/equation_registry_draft.json"
OUT = ROOT / "docs/phase2/evidence/evidence_register.json"

PREPARED_BY = (
    "Prepared by: Agent 5 (Research & Evidence Specialist), model: claude-opus-5-5 (rows EV-01 to EV-83); "
    "claude-sonnet-5-5 (rows EV-84 to EV-93, unit U-S3b; rows EV-94 to EV-105, unit U-S3c)"
)
ACCESSED_DEFAULT = "2026-10-04"
ACCESSED = {f"EV-{n}": "2026-10-08" for n in range(84, 106)}  # U-S3b and U-S3c lookups
STATUS_WEAKEST_FIRST = ["unresolved", "not tested", "assumption", "inferred", "verified"]
# Phase 1 status cells carry qualifiers; these phrases reduce to a vocabulary word.
STATUS_SYNONYMS = {"not accessed": "unresolved", "marketing": "unresolved"}
TOPOLOGIES = {
    "spiral": "planar spiral or concentric coils, including trapezoidal concentrated PCB coils",
    "wave": "wave windings with radial conductors and end turns (Xcoil interleaved wave)",
    "serpentine": "serpentine radial-conductor windings (Xcoil serpentine, ECM patents)",
    "distributed": "overlapping distributed PCB windings",
    "concentrated_wire": "wire-wound coreless concentrated coils (not PCB)",
    "general": "topology-independent physics, materials, manufacturing or method",
    "non_engineering": "licences, UI conventions, file formats; no winding physics",
}
KINDS = ["source_claim", "repository_fact", "bibliographic_record", "marketing_claim", "illustration"]
CITABLE_KINDS = {"source_claim", "repository_fact"}

T = {  # topology tags, one explicit entry per row so a new row cannot be silently untagged
    "EV-01": ["spiral"], "EV-02": ["spiral"], "EV-03": ["general"], "EV-04": ["spiral"], "EV-05": ["spiral"],
    "EV-06": ["spiral"], "EV-07": ["spiral"], "EV-08": ["general"], "EV-09": ["general"], "EV-10": ["spiral"],
    "EV-11": ["general"], "EV-12": ["spiral"], "EV-13": ["general"], "EV-14": ["spiral"], "EV-15": ["general"],
    "EV-16": ["general"], "EV-17": ["spiral"], "EV-18": ["wave", "distributed"], "EV-19": ["general"],
    "EV-20": ["general"], "EV-21": ["general"], "EV-22": ["general"], "EV-23": ["general"],
    "EV-24": ["distributed"], "EV-25": ["spiral"], "EV-26": ["distributed"], "EV-27": ["general"],
    "EV-28": ["spiral"], "EV-29": ["spiral"], "EV-30": ["general"], "EV-31": ["spiral"], "EV-32": ["general"],
    "EV-33": ["general"], "EV-34": ["wave"], "EV-35": ["general"], "EV-36": ["general"], "EV-37": ["general"],
    "EV-38": ["distributed"], "EV-39": ["general"], "EV-40": ["spiral"], "EV-41": ["spiral"],
    "EV-42": ["general"], "EV-43": ["spiral"], "EV-44": ["spiral"], "EV-45": ["general"], "EV-46": ["spiral"],
    "EV-47": ["concentrated_wire"], "EV-48": ["distributed"], "EV-49": ["general"], "EV-50": ["general"],
    "EV-51": ["spiral"], "EV-52": ["general"], "EV-53": ["general"], "EV-54": ["general"], "EV-55": ["general"],
    "EV-56": ["spiral", "concentrated_wire"], "EV-57": ["general"], "EV-58": ["general"], "EV-59": ["spiral"],
    "EV-60": ["spiral"], "EV-61": ["general"], "EV-62": ["spiral"], "EV-63": ["general"],
    "EV-64": ["serpentine"], "EV-65": ["serpentine", "spiral"], "EV-66": ["serpentine"], "EV-67": ["general"],
    "EV-68": ["general"], "EV-69": ["serpentine"], "EV-70": ["spiral", "wave"], "EV-71": ["wave"],
    "EV-72": ["non_engineering"], "EV-73": ["non_engineering"], "EV-74": ["non_engineering"],
    "EV-75": ["non_engineering"], "EV-76": ["non_engineering"], "EV-77": ["non_engineering"],
    "EV-78": ["general"], "EV-79": ["non_engineering"],
    "EV-R1": ["wave"], "EV-R2": ["wave"], "EV-R3": ["non_engineering"], "EV-R4": ["non_engineering"],
    "EV-R5": ["general"],
    "EV-K1": ["non_engineering"], "EV-K2": ["non_engineering"], "EV-K3": ["non_engineering"],
    "EV-K4": ["non_engineering"], "EV-K5": ["non_engineering"], "EV-K6": ["non_engineering"],
    "EV-80": ["general"], "EV-81": ["general"], "EV-82": ["general"], "EV-83": ["general"],
    "EV-84": ["general"], "EV-85": ["general"], "EV-86": ["general"], "EV-87": ["general"], "EV-88": ["general"],
    "EV-89": ["spiral", "wave"], "EV-90": ["spiral", "wave"], "EV-91": ["spiral"], "EV-92": ["general"],
    "EV-93": ["general"], "EV-94": ["general"], "EV-95": ["general"], "EV-96": ["general"], "EV-97": ["general"],
    "EV-98": ["general"], "EV-99": ["general"], "EV-100": ["general"], "EV-101": ["general"], "EV-102": ["general"],
    "EV-103": ["general"], "EV-104": ["wave"], "EV-105": ["wave"],
}
KIND = {  # rows that are not plain source claims
    "EV-60": "bibliographic_record", "EV-61": "bibliographic_record", "EV-63": "bibliographic_record",
    "EV-78": "bibliographic_record", "EV-69": "marketing_claim", "EV-70": "illustration",
    "EV-71": "repository_fact", "EV-R1": "repository_fact", "EV-R2": "repository_fact",
    "EV-R3": "repository_fact", "EV-R4": "repository_fact", "EV-R5": "repository_fact",
}
OUT_OF_SCOPE = {  # D-009 removed KiCad; these rows stay for traceability but the app never cites them
    "EV-79": "KiCad file format (D-009)", "EV-R4": "KiCad plugin architecture (D-009)",
    **{f"EV-K{i}": "KiCad integration (D-009)" for i in range(1, 7)},
}
JUDGEMENT_OVERRIDE = {"EV-43": ("partly", "via part applies; equal-flux assumption conflicts (G3)")}
NO_GAP_SCAN = {"EV-71"}  # "G1"/"G3" there are Gerber layer names, not gap ids
DOCS_FOR_ROW = {  # rows whose Source column names no D-number
    "EV-53": ["NBS-HB100"], "EV-54": ["ARNOLD-CAT"], "EV-55": ["ARNOLD-N42"], "EV-60": ["BIB-DAIPRE2006"],
    "EV-61": ["BIB-PYRHONEN"], "EV-63": ["BIB-BUMBY2005", "D10"], "EV-64": ["PAT-US10170953"],
    "EV-65": ["PAT-US11336130"], "EV-66": ["PAT-US9800109"], "EV-67": ["PAT-US10211694"],
    "EV-68": ["PAT-US12424901"], "EV-69": ["WEB-PCBSTATOR"], "EV-70": ["IMG-USER"],
    "EV-71": ["REPO-magnetless_motor"], "EV-72": ["WEB-NOTO"], "EV-73": ["WEB-LIBERATION"],
    "EV-74": ["WEB-CASCADIA"], "EV-75": ["WEB-JETBRAINS"], "EV-76": ["WEB-MANROPE"], "EV-77": ["WEB-IET-WM2004"],
    "EV-78": ["STD-ISO273"], "EV-79": ["WEB-KICAD-DEVDOCS", "REPO-kimotor"],
    "EV-R1": ["REPO-magnetless_motor"], "EV-R2": ["REPO-magnetless_motor"], "EV-R3": ["REPO-magnetless_motor"],
    "EV-R4": ["REPO-kimotor"], "EV-R5": ["REPO-kimotor"], "EV-K1": ["WEB-KICAD-DEVDOCS"],
    "EV-K2": ["WEB-KICAD-DEVDOCS"], "EV-K3": ["WEB-KICAD-DEVDOCS"], "EV-K4": ["PYPI-kicad-python"],
    "EV-K5": ["PYPI-kicad-python"], "EV-K6": ["WEB-KICAD-LICENCES"],
    "EV-80": ["MFR-HGT-NDFEB"], "EV-81": ["MFR-ARNOLD-SMMA2004"], "EV-82": ["THESIS-UARK2014"],
    "EV-83": ["MFR-BITTELE-TWC"],
    "EV-84": ["NIST-CODATA2022"], "EV-85": ["NIST-CODATA2022"], "EV-86": ["BIPM-SI-BROCHURE-9"],
    "EV-87": ["WEB-NBK-JISB1001"], "EV-88": ["WEB-AMESWEB-B1828"], "EV-89": ["BIB-TESSAROLO2019"],
    "EV-90": ["CONF-ALBERTI-MULTILAYER"], "EV-91": ["D09"], "EV-92": ["APN-MICROCHIP-AN955"],
    "EV-93": ["MFR-HGT-NDFEB"], "EV-94": ["MFR-ROGERS-RO4000"], "EV-95": ["MFR-DUPONT-KAPTONHN"],
    "EV-96": ["MFR-ISOLA-370HR"], "EV-97": ["MFR-ACCURATE-G10FR4"], "EV-98": ["MFR-BGM-FR4"],
    "EV-99": ["MFR-PLASTICSINTL-PTFE"], "EV-100": ["MFR-ELGIN-1018"], "EV-101": ["APN-ADI-MT003"],
    "EV-102": ["WEB-WIKI-THD"], "EV-103": ["WEB-MATHWORKS-THD"], "EV-104": ["GEARTECH-INVOLUTE2013"],
    "EV-105": ["WEB-MATHWORLD-CIRCLEINVOLUTE"],
}


def doc(id_, title, authors, year, year_text, venue, kind, url=None, path=None):
    return {"id": id_, "title": title, "authors": authors, "year": year, "year_text": year_text, "venue": venue,
            "kind": kind, "path": path, "url": url}


OTHER_DOCS = [
    doc("NBS-HB100", "Copper Wire Tables, Handbook 100", "U.S. National Bureau of Standards", 1966, "1966",
        "NBS Handbook 100", "standard", "https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook100.pdf"),
    doc("ARNOLD-CAT", "Sintered NdFeB catalog, Rev. 181031", "Arnold Magnetic Technologies", None, None,
        "manufacturer catalog", "datasheet",
        "https://www.arnoldmagnetics.com/wp-content/uploads/2017/10/Catalog-151021.pdf"),
    doc("ARNOLD-N42", "N42 datasheet, Rev. 210607", "Arnold Magnetic Technologies", None, None,
        "manufacturer datasheet", "datasheet",
        "https://www.arnoldmagnetics.com/wp-content/uploads/2017/11/N42-151021.pdf"),
    doc("BIB-DAIPRE2006", "Use of the star of slots in designing fractional-slot single-layer synchronous motors",
        "M. Dai Pre, N. Bianchi", 2006, "2006", "IEE Proc. Electr. Power Appl. 153(3) 459-466", "journal",
        "https://dialnet.unirioja.es/servlet/articulo?codigo=1979238"),
    doc("BIB-PYRHONEN", "Design of Rotating Electrical Machines", "J. Pyrhonen, T. Jokinen, V. Hrabovcova",
        None, None, "Wiley (edition not verified)", "textbook"),
    doc("BIB-BUMBY2005", "Axial-flux permanent-magnet air-cored generator for small-scale wind turbines",
        "J.R. Bumby, R. Martin", 2005, "2005", "IEE Proc. Electr. Power Appl. 152(5) 1065-1075", "journal",
        "https://digital-library.theiet.org/doi/10.1049/ip-epa:20050094"),
    doc("PAT-US10170953", "US 10,170,953 B2", "E-Circuit Motors (Shaw)", None, None, "US patent", "patent",
        "https://patents.google.com/patent/US10170953"),
    doc("PAT-US11336130", "US 11,336,130 B1", "E-Circuit Motors (Shaw, Milheim)", None, None, "US patent",
        "patent", "https://patents.justia.com/patent/11336130"),
    doc("PAT-US9800109", "US 9,800,109 and US 10,256,690", "E-Circuit Motors (Shaw)", None, None, "US patent",
        "patent", "https://patents.justia.com/patent/9800109"),
    doc("PAT-US10211694", "US 10,211,694", "E-Circuit Motors (Shaw)", None, None, "US patent", "patent",
        "https://patents.justia.com/patent/10211694"),
    doc("PAT-US12424901", "US 12,424,901 B2", "E-Circuit Motors (Shaw, Milheim)", None, None, "US patent",
        "patent", "https://patents.justia.com/patent/12424901"),
    doc("WEB-PCBSTATOR", "PCB stator technology pages", "E-Circuit Motors", None, None, "pcbstator.com",
        "marketing", "https://pcbstator.com/pcb-stator-technology/"),
    doc("IMG-USER", "User reference screenshots", "user", None, None, "reference images", "image",
        path="docs/phase1/evidence/reference_images/"),
    doc("REPO-magnetless_motor", "magnetless_motor @c6ec327e", "gouldpa00", 2026, "2026", "GitHub (GPL-3.0)",
        "repository", path="/home/claude/embodic-ref/magnetless_motor/"),
    doc("REPO-kimotor", "kimotor @dc6cac3a", "cooked", 2024, "2024", "GitHub (GPL-2.0-only)", "repository",
        path="/home/claude/embodic-ref/kimotor/"),
    doc("WEB-NOTO", "Noto Sans OFL.txt", "The Noto Project Authors", 2022, "2022", "notofonts", "licence",
        "https://github.com/notofonts/latin-greek-cyrillic/blob/main/OFL.txt"),
    doc("WEB-LIBERATION", "Liberation fonts LICENSE", "Google Corporation; Red Hat, Inc.", 2012, "2010-2012",
        "liberationfonts", "licence", "https://github.com/liberationfonts/liberation-fonts/blob/main/LICENSE"),
    doc("WEB-CASCADIA", "Cascadia Code LICENSE", "Microsoft Corporation", 2019, "2019", "microsoft/cascadia-code",
        "licence", "https://github.com/microsoft/cascadia-code/blob/main/LICENSE"),
    doc("WEB-JETBRAINS", "JetBrains Mono OFL.txt", "The JetBrains Mono Project Authors", 2020, "2020",
        "JetBrains/JetBrainsMono", "licence", "https://github.com/JetBrains/JetBrainsMono/blob/master/OFL.txt"),
    doc("WEB-MANROPE", "Manrope OFL.txt", "The Manrope Project Authors", 2018, "2018", "google/fonts", "licence",
        "https://github.com/google/fonts/blob/main/ofl/manrope/OFL.txt"),
    doc("WEB-IET-WM2004", "Harmonised colours and alphanumeric marking", "IET Wiring Matters", 2004, "2004",
        "IET Wiring Matters, Spring 2004", "magazine",
        "https://electrical.theiet.org/media/1720/harmonised-colours-and-alphanumeric-marketing.pdf"),
    doc("STD-ISO273", "ISO 273:1979 Fasteners - Clearance holes for bolts and screws", "ISO/TC 2/SC 7", 1979,
        "1979", "ISO", "standard", "https://www.iso.org/standard/4183.html"),
    doc("WEB-KICAD-DEVDOCS", "KiCad developer documentation", "KiCad project", None, None, "dev-docs.kicad.org",
        "documentation", "https://dev-docs.kicad.org/"),
    doc("PYPI-kicad-python", "kicad-python 0.8.0", "KiCad project", None, None, "PyPI", "package",
        "https://pypi.org/project/kicad-python/"),
    doc("WEB-KICAD-LICENCES", "KiCad licenses", "KiCad project", None, None, "kicad.org", "documentation",
        "https://www.kicad.org/about/licenses/"),
    doc("MFR-HGT-NDFEB", "Sintered NdFeB Magnets' Specifications", "HGT Advanced Magnets Co., Ltd", None, None,
        "manufacturer specification sheet (no revision or date printed)", "datasheet",
        "https://www.advancedmagnets.com/wp-content/uploads/2020/07/"
        "Sintered-Neodymium-Iron-Boron-NdFeB-Magnets-Specifications.pdf"),
    doc("MFR-ARNOLD-SMMA2004", "NdFeB for High Temperature Motor Applications", "S. Constantinides, D. Gulick",
        2004, "2004", "SMMA Fall Technical Conference, 3-5 Nov 2004 (Arnold Magnetic Technologies slides)",
        "presentation",
        "https://www.arnoldmagnetics.com/wp-content/uploads/2017/10/NdFeB-for-high-temperature-motor-applications.pdf"),
    doc("THESIS-UARK2014", "Design, Simulation and Implementation of Three-Phase Bidirectional DC-DC Dual Active "
        "Bridge Converter Using SiC MOSFETs", "T. Aldawsari", 2014, "2014",
        "MSc thesis, Electrical Engineering, University of Arkansas", "thesis",
        "https://scholarworks.uark.edu/cgi/viewcontent.cgi?article=3596&context=etd"),
    doc("MFR-BITTELE-TWC", "Trace Width Calculator", "Bittele Electronics", None, None,
        "PCB manufacturer web page", "manufacturer_page", "https://www.7pcb.com/trace-width-calculator"),
    doc("NIST-CODATA2022", "Fundamental Physical Constants, Complete Listing (2022 CODATA adjustment)",
        "NIST", 2022, "2022", "physics.nist.gov, allascii.txt", "reference_data",
        "https://physics.nist.gov/cuu/Constants/Table/allascii.txt"),
    doc("BIPM-SI-BROCHURE-9", "SI Brochure, 9th edition (edition number from the file name; title page not read)",
        "BIPM (host bipm.org)", None, None, "bipm.org, SI-Brochure-9-EN.pdf", "standard",
        "https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf"),
    doc("WEB-NBK-JISB1001", "Technical data 20: Diameter of clearance holes and counterbores for bolts and screws "
        "(JIS B 1001 table)", "NBK (manufacturer)", 2015, "2015-06-18", "manufacturer technical page",
        "manufacturer_page",
        "https://alb02.internal.nbk1560.com/en/resources/other/article/"
        "technical-20-diameter-of-clearance-holes-and-counterbores-for-bolts-and-screws"),
    doc("WEB-AMESWEB-B1828", "Metric Clearance Hole Chart (cites ASME B18.2.8-1999)", "AmesWeb", None, None,
        "web page", "web_page", "https://amesweb.info/Screws/Metric-Clearance-Hole-Chart.aspx"),
    doc("BIB-TESSAROLO2019", "Investigation Into Multi-Layer Fractional-Slot Concentrated Windings With "
        "Unconventional Slot-Pole Combinations", "A. Tessarolo, C. Ciriani, M. Bortolozzi, M. Mezzarobba, N. Barbini",
        2019, "2019", "IEEE Trans. Energy Convers. 34(4) 1985-1996, doi 10.1109/TEC.2019.2929950", "journal",
        "https://arts.units.it/bitstream/11368/2958612/4/2958612_IEEE%20TEC%202019-PostPrint.pdf"),
    doc("CONF-ALBERTI-MULTILAYER", "Theory and Design of Fractional-Slot Multilayer Windings",
        "L. Alberti, N. Bianchi", None, "unresolved",
        "Presentation, University of Padova; the extract says ECCE 2011 Phoenix, the file name says ECCE 2010",
        "presentation", "https://research.unipd.it/bitstream/11577/2514240/1/ECCE_2010_Multilayer_presentation_web.pdf"),
    doc("APN-MICROCHIP-AN955", "VF Control of 3-Phase Induction Motor Using Space Vector Modulation, AN955 "
        "(DS00955A)", "R. Parekh (Microchip Technology)", 2005, "2005",
        "application note (copy hosted on mikrocontroller.net)", "application_note",
        "https://mikrocontroller.net/attachment/337300/AN955.pdf"),
    doc("MFR-ROGERS-RO4000", "RO4000 Series High Frequency Circuit Materials, data sheet (Revised 1592 080322, "
        "PUB# 92-004)", "Rogers Corporation", 2022, "2022 (copyright line)", "manufacturer data sheet", "datasheet",
        "https://www.rogerscorp.com/-/media/project/rogerscorp/documents/advanced-electronics-solutions/english/"
        "data-sheets/ro4000-laminates-ro4003c-and-ro4350b---data-sheet.pdf"),
    doc("MFR-DUPONT-KAPTONHN", "Kapton HN polyimide film data sheet, K-15345-2 (12/16)", "DuPont", 2016, "2016",
        "manufacturer data sheet (copy hosted at epectec.com)", "datasheet",
        "https://www.epectec.com/downloads/DuPont-Kapton-HN-Polyimide-Film.pdf"),
    doc("MFR-ISOLA-370HR", "370HR Industry Leading, Standard Loss, Thermally Robust Epoxy Laminate and Prepreg",
        "Isola Group", 2021, "2021 (footer: Revision C, Last Updated April 15, 2021)", "manufacturer data sheet",
        "datasheet", "https://www.isola-group.com/wp-content/uploads/data-sheets/370hr.pdf"),
    doc("MFR-ACCURATE-G10FR4", "Acculam Epoxyglas G10, FR4, Product Data Sheet", "Accurate Plastics "
        "(distributed by Polymershapes)", None, None, "manufacturer data sheet (no date printed)", "datasheet",
        "https://www.polymershapes.com/wp-content/uploads/2020/04/"
        "Polymershapes_Accurate_DataSheet-Acculam-Epoxyglas-G10-FR4.pdf"),
    doc("MFR-BGM-FR4", "G10/FR4 Data Sheet", "BGM International LLC", None, None,
        "manufacturer data sheet (copy hosted at curbellplastics.com; no date printed)", "datasheet",
        "https://www.curbellplastics.com/wp-content/uploads/2024/04/BGM-International-FR4-Data-Sheet.pdf"),
    doc("MFR-PLASTICSINTL-PTFE", "PTFE data sheet", "Plastics International (the document names no issuer)", None,
        None, "distributor data sheet (no date printed)", "datasheet",
        "https://www.plasticsintl.com/media/trshlm53/ptfe-data-sheet.pdf"),
    doc("MFR-ELGIN-1018", "Carbon Steel Grade 1018 Data Sheet", "Elgin (from the file name; the page names no "
        "issuer)", None, None, "distributor data sheet (copy hosted at mwcomponents.com)", "datasheet",
        "https://www.mwcomponents.com/uploads/Resource-Center/Elgin-Material-Sheets/"
        "Carbon-Steel-Grade-1018-Data-Sheet_Elgin.pdf"),
    doc("APN-ADI-MT003", "Understand SINAD, ENOB, SNR, THD, THD + N, and SFDR so You Don't Get Lost in the Noise "
        "Floor, MT-003 Rev. A 10/08", "W. Kester (Analog Devices)", 2009, "2009 (copyright line)",
        "manufacturer tutorial", "application_note",
        "https://www.analog.com/media/en/training-seminars/tutorials/MT-003.pdf"),
    doc("WEB-WIKI-THD", "Total harmonic distortion", "Wikipedia contributors", None, None, "Wikipedia", "web_page",
        "https://en.wikipedia.org/wiki/Total_harmonic_distortion"),
    doc("WEB-MATHWORKS-THD", "thd - Total harmonic distortion - MATLAB", "MathWorks", None, None,
        "MATLAB Signal Processing Toolbox documentation", "documentation",
        "https://www.mathworks.com/help/signal/ref/thd.html"),
    doc("GEARTECH-INVOLUTE2013", "Involute (Back to Basics)", "Gear Technology (adapted from U. Hindhede 1989 and "
        "H. W. Van Gerpen, C. K. Reece 1988)", 2013, "2013", "Gear Technology, January/February 2013, p. 88",
        "magazine", "https://ik.imagekit.io/agmamedia/gt/issues/0113x/involute_curve_basics.pdf"),
    doc("WEB-MATHWORLD-CIRCLEINVOLUTE", "Circle Involute", "Wolfram MathWorld", None, None, "mathworld.wolfram.com",
        "web_page", "https://mathworld.wolfram.com/CircleInvolute.html"),
]


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def plain(text: str) -> str:
    return text.replace("**", "").replace("`", "")


def parse_documents(md: str) -> list[dict]:
    out = []
    for line in md.splitlines():
        if not re.match(r"\| D\d\d \|", line):
            continue
        c = cells(line)
        if len(c) != 6:
            raise ValueError(f"document row has {len(c)} cells: {line[:60]}")
        venue = plain(c[4])
        no_doi = re.sub(r"(?i)doi \S+", "", venue)
        years = sorted(set(re.findall(r"\b(?:19|20)\d\d\b", no_doi)))
        if "unresolved" in venue or not years:
            year, year_text = None, "unresolved"
        elif len(years) == 1:
            year, year_text = int(years[0]), years[0]
        else:
            year, year_text = None, "-".join(years)
        kind = "thesis" if "dissertation" in venue.lower() else "review" if "Review" in c[2] else "paper"
        out.append(doc(c[0], plain(c[2]), plain(c[3]), year, year_text, venue, kind, path=plain(c[1])))
    return out


def single_status(cell: str) -> str:
    low = plain(cell).lower()
    found = {word for word in STATUS_WEAKEST_FIRST if word in low}
    found |= {label for phrase, label in STATUS_SYNONYMS.items() if phrase in low}
    if not found:
        raise ValueError(f"status cell maps to no vocabulary word: {cell}")
    return next(word for word in STATUS_WEAKEST_FIRST if word in found)


def judgement(ev_id: str, applies: str) -> str:
    if ev_id in JUDGEMENT_OVERRIDE:
        return JUDGEMENT_OVERRIDE[ev_id][0]
    low = plain(applies).lower()
    rules = [("yes/partly", "partly"), ("yes", "yes"), ("partly", "partly"), ("internal inconsistency", "partly"),
             ("doubtful", "no"), ("conflicts", "no"), ("context only", "no"), ("illustrative only", "no"),
             ("do not reuse", "no"), ("reference only", "no"), ("architecture reference only", "no")]
    for prefix, verdict in rules:
        if low.startswith(prefix):
            return verdict
    raise ValueError(f"{ev_id}: applies cell matches no rule: {applies[:60]}")


def read_method(status: str, location: str, applies: str) -> str:
    s = plain(status).lower()
    if "parse" in s:
        return "parse"
    if "source read" in s:
        return "source_read"
    if "extract" in s:
        return "webfetch_extract"
    if "(img)" in location or "(img" in location or "(img)" in applies:
        return "img"
    if "image" in s:
        return "image_view"
    return "text"


def location(text: str, source: str) -> dict:
    t = plain(text)
    pages: list[int] = []
    for a, b in re.findall(r"\bp\.\s?(\d+)(?:\s?[–-]\s?(\d+))?", t):
        pages.extend(range(int(a), int(b or a) + 1))
    printed = re.findall(r"(?:printed|journal) (\d+(?:[–-]\d+)?)", t)
    urls = [u.rstrip(";,)") for u in re.findall(r"https?://\S+", plain(source) + " " + t)]
    return {"text": t, "pages_pdf": sorted(set(pages)), "pages_printed": ", ".join(printed) or None,
            "urls": sorted(set(urls))}


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    p1, p2 = PHASE1_MD.read_text(), PHASE2_MD.read_text()
    documents = parse_documents(p1) + OTHER_DOCS
    by_doc = {d["id"]: d for d in documents}
    eq = json.loads(EQ_REGISTRY.read_text())
    eqs_for_ev: dict[str, list[str]] = {}
    for e in eq["equations"]:
        for ev in e.get("sources", []):
            eqs_for_ev.setdefault(ev, []).append(e["id"])

    entries = []
    for origin, md in (("phase1", p1), ("phase2", p2)):
        for line in md.splitlines():
            if not re.match(r"\| EV-[0-9RK]+\d* \|", line):
                continue
            c = cells(line)
            if len(c) != 6:
                raise ValueError(f"EV row has {len(c)} cells: {line[:60]}")
            ev_id, claim, source, loc, applies, status = c
            docs = DOCS_FOR_ROW.get(ev_id) or sorted(set(re.findall(r"\bD\d\d\b", source)))
            if not docs:
                raise ValueError(f"{ev_id}: no document id")
            kind = KIND.get(ev_id, "source_claim")
            scope_reason = OUT_OF_SCOPE.get(ev_id)
            first = by_doc[docs[0]]
            text_all = " ".join((claim, applies, status))
            gaps = [] if ev_id in NO_GAP_SCAN else sorted(set(re.findall(r"\bG\d{1,2}\b", plain(text_all))),
                                                            key=lambda g: int(g[1:]))
            note = plain(applies)
            if ev_id in JUDGEMENT_OVERRIDE:
                note += f" [judgement override: {JUDGEMENT_OVERRIDE[ev_id][1]}]"
            entries.append({
                "id": ev_id,
                "claim": plain(claim),
                "kind": kind,
                "source": {"document": first["id"], "title": first["title"], "authors": first["authors"],
                           "year": first["year"], "year_text": first["year_text"]},
                "documents": docs,
                "location": location(loc, source),
                "read_method": read_method(status, loc, applies),
                "applies": {"judgement": judgement(ev_id, applies), "note": note, "status": "inferred"},
                "status": single_status(status),
                "status_note": plain(status),
                "topology_tags": T[ev_id],
                "phase2_scope": scope_reason is None,
                "out_of_scope_reason": scope_reason,
                "citable": kind in CITABLE_KINDS and scope_reason is None,
                "related_equations": eqs_for_ev.get(ev_id, []),
                "related_gaps": gaps,
                "register_origin": origin,
                "accessed": ACCESSED.get(ev_id, ACCESSED_DEFAULT),
            })

    return {
        "prepared_by": PREPARED_BY,
        "schema": "embodic evidence register",
        "schema_version": 1,
        "generated_by": "docs/phase2/evidence/tools/build_evidence_register.py",
        "generated_from": [
            {"path": str(p.relative_to(ROOT)), "sha256": file_digest(p)} for p in (PHASE1_MD, PHASE2_MD, EQ_REGISTRY)
        ],
        "status_vocabulary": STATUS_WEAKEST_FIRST[::-1],
        "status_order_weakest_first": STATUS_WEAKEST_FIRST,
        "status_meaning": "read in the source (or reproduced by running something) by Agent 5; never physical "
                          "correctness and never experimental confirmation. Weakest qualifier in the Phase 1 "
                          "status cell wins; the full cell is kept in status_note.",
        "topology_vocabulary": TOPOLOGIES,
        "kind_vocabulary": KINDS,
        "citable_rule": "citable = kind in [source_claim, repository_fact] and phase2_scope",
        "documents": documents,
        "entries": entries,
    }


def check(reg: dict) -> list[str]:
    errors = []
    ids = [e["id"] for e in reg["entries"]]
    doc_ids = {d["id"] for d in reg["documents"]}
    if len(ids) != len(set(ids)):
        errors.append("duplicate EV ids")
    for e in reg["entries"]:
        if e["status"] not in STATUS_WEAKEST_FIRST:
            errors.append(f"{e['id']}: bad status")
        if not e["topology_tags"] or any(t not in TOPOLOGIES for t in e["topology_tags"]):
            errors.append(f"{e['id']}: bad topology tags")
        if e["kind"] not in KINDS:
            errors.append(f"{e['id']}: bad kind")
        errors += [f"{e['id']}: unknown document {d}" for d in e["documents"] if d not in doc_ids]
    for table, name in ((T, "T"), (KIND, "KIND"), (OUT_OF_SCOPE, "OUT_OF_SCOPE"), (DOCS_FOR_ROW, "DOCS_FOR_ROW")):
        errors += [f"{name} names missing row {k}" for k in table if k not in ids]
    eq = json.loads(EQ_REGISTRY.read_text())
    cited = {ev for e in eq["equations"] for ev in e.get("sources", [])}
    errors += [f"equation registry cites missing {ev}" for ev in sorted(cited - set(ids))]
    text = json.dumps(reg, ensure_ascii=False)
    if re.search("[\\u0e00-\\u0e7f]", text):
        errors.append("Thai characters present")
    return errors


def main() -> None:
    reg = build()
    errors = check(reg)
    if errors:
        raise SystemExit("refusing to write:\n" + "\n".join(errors))
    OUT.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n")
    entries = reg["entries"]

    def count(key: str) -> dict:
        return {v: sum(1 for e in entries if e[key] == v) for v in sorted({e[key] for e in entries})}

    print(f"wrote {OUT.relative_to(ROOT)}: {len(entries)} entries, {len(reg['documents'])} documents")
    print("status:", count("status"))
    print("kind:", count("kind"))
    print("phase2_scope:", count("phase2_scope"), "citable:", count("citable"))


if __name__ == "__main__":
    main()
