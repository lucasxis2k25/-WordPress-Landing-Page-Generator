from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Any, Iterator


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CELL_REF_RE = re.compile(r"^([A-Z]+)([0-9]+)$")


def qname(local: str) -> str:
    return f"{{{MAIN_NS}}}{local}"


def column_letters(cell_ref: str) -> str:
    match = CELL_REF_RE.match(cell_ref)
    if not match:
        raise ValueError(f"Invalid cell reference: {cell_ref}")
    return match.group(1)


def column_index(column: str) -> int:
    result = 0
    for char in column:
        result = result * 26 + ord(char) - 64
    return result


def coerce_value(value: str | None) -> Any:
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return ""
    try:
        if re.fullmatch(r"[-+]?\d+", value):
            return int(value)
        if re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[Ee][-+]?\d+)?", value):
            return float(value)
    except ValueError:
        pass
    return value


@dataclass(frozen=True)
class SheetSnapshot:
    name: str
    xml_path: str
    rows: tuple[dict[str, Any], ...]
    formula_count: int

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def max_col(self) -> int:
        return max((column_index(col) for row in self.rows for col in row), default=0)


@dataclass(frozen=True)
class WorkbookSnapshot:
    sheets: tuple[SheetSnapshot, ...]
    shared_string_count: int
    source_path: str

    def sheet(self, name: str) -> SheetSnapshot:
        for sheet in self.sheets:
            if sheet.name == name:
                return sheet
        raise KeyError(f"Worksheet not found: {name!r}")

    def find_sheet(self, *tokens: str) -> SheetSnapshot:
        normalized = [token.casefold() for token in tokens]
        for sheet in self.sheets:
            haystack = sheet.name.casefold()
            if all(token in haystack for token in normalized):
                return sheet
        raise KeyError(f"No worksheet matched tokens: {tokens}")


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return ["".join(t.text or "" for t in item.iter(qname("t"))) for item in root.findall(qname("si"))]


def _cell_value(cell: ET.Element, shared_strings: list[str]) -> Any:
    value_node = cell.find(qname("v"))
    cell_type = cell.attrib.get("t")
    if value_node is not None:
        raw = value_node.text
        if cell_type == "s" and raw is not None:
            return shared_strings[int(raw)]
        if cell_type == "b":
            return raw == "1"
        return coerce_value(raw)
    if cell_type == "inlineStr":
        return "".join(t.text or "" for t in cell.iter(qname("t")))
    return None


def _target_path(target: str) -> str:
    target = target.lstrip("/")
    return target if target.startswith("xl/") else f"xl/{target}"


def read_workbook(path: str | Path) -> WorkbookSnapshot:
    """Read every worksheet and every non-empty cell once, using cached XLSX values.

    Formula text is intentionally not evaluated. If the workbook contains a cached
    value, that value is captured; Excel is never used as a calculation engine.
    """
    source = Path(path)
    with zipfile.ZipFile(source) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels.findall(f"{{{PKG_REL_NS}}}Relationship")
        }
        shared_strings = _shared_strings(archive)
        sheets: list[SheetSnapshot] = []
        for sheet in workbook.findall(f"{qname('sheets')}/{qname('sheet')}"):
            name = sheet.attrib["name"]
            target = _target_path(rel_map[sheet.attrib[f"{{{REL_NS}}}id"]])
            root = ET.fromstring(archive.read(target))
            rows: list[dict[str, Any]] = []
            formula_count = 0
            for row_node in root.findall(f".//{qname('sheetData')}/{qname('row')}"):
                row: dict[str, Any] = {}
                for cell in row_node.findall(qname("c")):
                    ref = cell.attrib.get("r")
                    if not ref:
                        continue
                    value = _cell_value(cell, shared_strings)
                    row[column_letters(ref)] = value
                    formula_count += int(cell.find(qname("f")) is not None)
                rows.append(row)
            sheets.append(SheetSnapshot(name, target, tuple(rows), formula_count))
    return WorkbookSnapshot(tuple(sheets), len(shared_strings), str(source))


def iter_sheet_rows(sheet: SheetSnapshot, start_row: int = 1) -> Iterator[tuple[int, dict[str, Any]]]:
    for row_number, row in enumerate(sheet.rows, start=1):
        if row_number >= start_row:
            yield row_number, row
