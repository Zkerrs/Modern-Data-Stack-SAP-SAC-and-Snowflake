"""
Regenera, em sequencia, os CSV das views standard I_* deste repositorio:
  I_Customer → I_Supplier (derivado do primeiro) → I_CompanyCode.

Executar na raiz do projeto:
  python src/generate_all_i_views.py
  python src/generate_all_i_views.py --quick
  python src/generate_all_i_views.py --rows 130000
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from sap_synthetic_masters import (
    I_CUSTOMER_DEFAULT_ROWS,
    I_CUSTOMER_MAX_ROWS,
    I_CUSTOMER_MIN_ROWS,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenera I_Customer, I_Supplier e I_CompanyCode em data/."
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="I_Customer em modo teste (600 linhas via --quick no gerador).",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=None,
        metavar="N",
        help=(
            f"Linhas I_Customer; fora de --quick ajustado a [{I_CUSTOMER_MIN_ROWS}, {I_CUSTOMER_MAX_ROWS}]. "
            f"Sem --rows o padrao e {I_CUSTOMER_DEFAULT_ROWS}."
        ),
    )
    args = parser.parse_args()

    if args.quick:
        if args.rows is not None:
            print("Aviso: --quick ignora --rows.", file=sys.stderr, flush=True)
        customer_cmd_tail = ["--quick"]
    else:
        requested = args.rows if args.rows is not None else I_CUSTOMER_DEFAULT_ROWS
        if requested < I_CUSTOMER_MIN_ROWS:
            print(
                f"Aviso: --rows={requested} abaixo do minimo; ajustado a {I_CUSTOMER_MIN_ROWS}.",
                file=sys.stderr,
                flush=True,
            )
        if requested > I_CUSTOMER_MAX_ROWS:
            print(
                f"Aviso: --rows={requested} acima do maximo; ajustado a {I_CUSTOMER_MAX_ROWS}.",
                file=sys.stderr,
                flush=True,
            )
        customer_rows = max(I_CUSTOMER_MIN_ROWS, min(requested, I_CUSTOMER_MAX_ROWS))
        customer_cmd_tail = ["--rows", str(customer_rows)]

    exe = sys.executable
    data = ROOT / "data"
    steps: list[list[str]] = [
        [
            exe,
            str(ROOT / "src" / "generate_i_customer_csv.py"),
            *customer_cmd_tail,
            "--output",
            str(data / "I_Customer.csv"),
        ],
        [
            exe,
            str(ROOT / "src" / "generate_i_supplier_csv.py"),
            "--from-customer-csv",
            str(data / "I_Customer.csv"),
            "--output",
            str(data / "I_Supplier.csv"),
        ],
        [
            exe,
            str(ROOT / "src" / "generate_i_companycode_csv.py"),
            "--output",
            str(data / "I_CompanyCode.csv"),
        ],
    ]

    data.mkdir(parents=True, exist_ok=True)
    for cmd in steps:
        print("+", " ".join(cmd), flush=True)
        r = subprocess.run(cmd, cwd=str(ROOT), check=False)
        if r.returncode != 0:
            print(f"Falhou (codigo {r.returncode}).", file=sys.stderr)
            return r.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
