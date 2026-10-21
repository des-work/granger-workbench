"""Data digest — summarize big CSV/Excel files CHEAPLY. Instead of feeding
thousands of raw rows to a paid model, Ultra-PC (via pandas) reports the shape,
column schema/dtypes, summary statistics, null counts, and a small sample — so
the assistant reads a compact profile, not the whole dataset.

    python ultra.py data <file.csv|xlsx> [--rows N] [--out f.md]
"""

from __future__ import annotations

from pathlib import Path

from . import core, ui


def _load(path: Path, sheet=0):
    import pandas as pd
    ext = path.suffix.lower()
    if ext in (".xlsx", ".xlsm", ".xls"):
        return pd.read_excel(path, sheet_name=sheet)
    if ext in (".tsv",):
        return pd.read_csv(path, sep="\t")
    return pd.read_csv(path)


def summarize(path: str, sample: int = 5) -> str:
    import pandas as pd
    p = Path(path).expanduser()
    ext = p.suffix.lower()
    out = [f"# DATA DIGEST: {p.name}"]

    # list Excel sheets so nothing is hidden
    sheets = [None]
    if ext in (".xlsx", ".xlsm", ".xls"):
        try:
            xl = pd.ExcelFile(p)
            sheets = xl.sheet_names
            out.append(f"Sheets: {', '.join(sheets)}")
        except Exception:
            sheets = [0]

    for sh in sheets:
        try:
            df = _load(p, sheet=sh if sh is not None else 0)
        except Exception as exc:
            out.append(f"\n(could not read sheet {sh}: {exc})")
            continue
        name = f" [{sh}]" if sh not in (None, 0) else ""
        out.append(f"\n## Table{name}: {df.shape[0]:,} rows × {df.shape[1]} cols")

        out.append("\nColumns (name · dtype · nulls · sample):")
        for c in df.columns:
            col = df[c]
            nulls = int(col.isna().sum())
            ex = col.dropna().head(1)
            exval = str(ex.iloc[0])[:40] if len(ex) else ""
            out.append(f"  - {str(c)[:32]:<32} {str(col.dtype):<10} "
                       f"nulls={nulls:<6} e.g. {exval}")

        num = df.select_dtypes("number")
        if not num.empty:
            desc = num.describe().round(3)
            out.append("\nNumeric summary:")
            out.append(desc.to_string())

        cat = df.select_dtypes(include=["object", "category"])
        if not cat.empty:
            out.append("\nTop categories:")
            for c in cat.columns[:8]:
                vc = df[c].value_counts().head(5)
                pairs = ", ".join(f"{str(k)[:20]}({v})" for k, v in vc.items())
                out.append(f"  {str(c)[:24]}: {pairs}")

        out.append(f"\nSample ({min(sample, len(df))} rows):")
        out.append(df.head(sample).to_string(max_colwidth=24))
    return "\n".join(out) + "\n"


def cmd_data(path: str, out=None, sample=5) -> int:
    p = Path(path).expanduser()
    if not p.exists():
        print(f"Not found: {p}"); return 1
    try:
        text = summarize(str(p), sample=sample)
    except ImportError:
        print("pandas is required (pip install pandas openpyxl)."); return 1
    except Exception as exc:
        print(f"Could not summarize {p.name}: {exc}"); return 1
    if out:
        Path(out).expanduser().write_text(text, encoding="utf-8")
        print(f"Wrote data digest (~{len(text)//4:,} tokens) -> {out}")
    else:
        print(text)
    return 0


def _tool_data(ctx=None) -> None:
    ui.title_bar("Data digest — profile a CSV/Excel file")
    f = ui.ask_open_file("Choose a data file",
                         [("Data", "*.csv *.tsv *.xlsx *.xlsm *.xls"),
                          ("All files", "*.*")])
    if not f:
        ui.pause(); return
    print()
    cmd_data(f)
    ui.pause()


def register_tool(cat) -> None:
    cat.add("data", "Data digest (profile a big CSV/Excel)", _tool_data)


def handle(argv: list[str]) -> int | None:
    if not argv or argv[0].lower() != "data":
        return None
    rest = argv[1:]
    out, sample, pos = None, 5, []
    i = 0
    while i < len(rest):
        if rest[i] == "--out" and i + 1 < len(rest):
            out = rest[i + 1]; i += 2
        elif rest[i] == "--rows" and i + 1 < len(rest):
            sample = int(rest[i + 1]); i += 2
        else:
            pos.append(rest[i]); i += 1
    if not pos:
        print("usage: data <file.csv|xlsx> [--rows N] [--out f]"); return 2
    return cmd_data(pos[0], out=out, sample=sample)
