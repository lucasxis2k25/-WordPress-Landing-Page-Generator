from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
import zipfile
import xml.etree.ElementTree as ET


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def qname(local: str) -> str:
    return f"{{{MAIN_NS}}}{local}"


def col_index(cell_ref: str) -> int:
    letters = "".join(c for c in cell_ref if c.isalpha())
    result = 0
    for char in letters:
        result = result * 26 + ord(char.upper()) - 64
    return result


def read_workbook(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels.findall(f"{{{PKG_REL_NS}}}Relationship")
        }

        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in strings.findall(qname("si")):
                shared_strings.append("".join(t.text or "" for t in item.iter(qname("t"))))

        sheets: list[dict[str, Any]] = []
        for sheet in workbook.findall(f"{qname('sheets')}/{qname('sheet')}"):
            sheet_name = sheet.attrib["name"]
            target = rel_map[sheet.attrib[f"{{{REL_NS}}}id"]].lstrip("/")
            if not target.startswith("xl/"):
                target = f"xl/{target}"
            root = ET.fromstring(archive.read(target))
            rows: list[dict[str, Any]] = []
            max_col = 0
            formula_count = 0
            for row in root.findall(f".//{qname('sheetData')}/{qname('row')}"):
                values: dict[str, Any] = {}
                for cell in row.findall(qname("c")):
                    ref = cell.attrib["r"]
                    value_node = cell.find(qname("v"))
                    formula_node = cell.find(qname("f"))
                    value: Any = None
                    if value_node is not None:
                        value = value_node.text
                        if cell.attrib.get("t") == "s":
                            value = shared_strings[int(value)]
                    elif cell.attrib.get("t") == "inlineStr":
                        value = "".join(t.text or "" for t in cell.iter(qname("t")))
                    if formula_node is not None:
                        formula_count += 1
                    values[ref] = {"value": value, "formula": formula_node.text if formula_node is not None else None}
                    max_col = max(max_col, col_index(ref))
                rows.append(values)
            sheets.append(
                {
                    "name": sheet_name,
                    "xml": target,
                    "row_count": len(rows),
                    "max_col": max_col,
                    "formula_count": formula_count,
                    "rows": rows,
                }
            )
        return {"sheets": sheets, "shared_string_count": len(shared_strings)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--sheet", action="append", default=[])
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    payload = read_workbook(args.path)
    selected = set(args.sheet)
    if selected:
        payload["sheets"] = [sheet for sheet in payload["sheets"] if sheet["name"] in selected]
    if not args.full:
        for sheet in payload["sheets"]:
            rows = sheet["rows"]
            sheet["rows"] = rows[:8] + ([] if len(rows) <= 13 else [{"...": "..."}]) + rows[-5:]
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
