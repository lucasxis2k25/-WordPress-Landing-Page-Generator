from __future__ import annotations

import json
from pathlib import Path

from .pilot import PILOT_PRODUCTS, run_pilot


def run_corrected(input_parquet: str, data_dir: str, output_dir: str):
    result = run_pilot(input_parquet, data_dir, output_dir, PILOT_PRODUCTS)
    destination = Path(output_dir)
    for item in result["results"]:
        item["differences"]["new_technical_family"] = True
        item["differences"]["technical_family_requires_approval"] = True
    result["manifest"]["technical_family_approval_required"] = True
    result["manifest"]["published"] = False
    destination.joinpath("pilot_results.json").write_text(json.dumps(result["results"], ensure_ascii=False, indent=2), encoding="utf-8")
    destination.joinpath("differences.json").write_text(json.dumps([{"product": item["product"], **item["differences"]} for item in result["results"]], ensure_ascii=False, indent=2), encoding="utf-8")
    destination.joinpath("pilot_manifest.json").write_text(json.dumps(result["manifest"], ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    final = run_corrected(args.input, args.data_dir, args.output_dir)
    print(json.dumps({"products_processed": final["manifest"]["products_processed"], "research_queue_count": final["manifest"]["research_queue_count"], "new_terms_count": final["manifest"]["new_terms_count"], "published": final["manifest"]["published"]}, ensure_ascii=False, indent=2))
