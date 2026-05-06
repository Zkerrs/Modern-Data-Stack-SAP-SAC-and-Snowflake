"""
CSV sintetico espelho da view standard `I_GLAccount` (Conta Contabil).

- Em codigo, mantem-se lista ampla de campos no padrao OData/CDS (PascalCase).
- No CSV final, remove-se apenas coluna 100% vazia em todas as linhas.
- Fora de --quick, volume e ajustado para faixa 120k-150k.

Uso:
  python src/generate_i_glaccount_csv.py [--rows N] --output data/I_GLAccount.csv
"""

from __future__ import annotations

import argparse
import csv
import random
import re
import string
import sys
from datetime import datetime, timedelta
from pathlib import Path

from sap_synthetic_masters import (
    MASTER_CLIENT_IDS,
    MASTER_GL_ACCOUNTS,
    SYNTHETIC_MASTER_SEED,
    csv_cell_has_semantic_value,
)

# Ordem de campos mantida no padrao de view.
GLACCOUNT_COLUMNS = [
    "Client",
    "ChartOfAccounts",
    "GLAccount",
    "GLAccountName",
    "GLAccountLongName",
    "AlternativeGLAccount",
    "CountryChartOfAccounts",
    "AccountType",
    "GLAccountType",
    "GLAccountGroup",
    "IsBalanceSheetAccount",
    "ProfitLossAccountType",
    "RetainedEarningsAccount",
    "CorporateGroupAccount",
    "FunctionalArea",
    "ConsolidationChartOfAccounts",
    "ConsolidationAccount",
    "ExchangeRateType",
    "TranslationDateType",
    "PlanningAccount",
    "AccountCurrency",
    "CashFlowStatementAccount",
    "CreatedByUser",
    "CreationDate",
    "LastChangedByUser",
    "LastChangeDate",
    "AccountIsMarkedForDeletion",
    "IsBlockedForCreation",
    "IsBlockedForPosting",
    "IsBlockedForPlanning",
    "IsOpenItemManaged",
    "IsLineItemDisplayed",
    "LineItemTaxDisplayOnly",
    "ReconciliationAccountIsReqd",
    "ReconciliationAccountType",
    "OpenItemClrngIsUsed",
    "SortKey",
    "FieldStatusGroup",
    "PostAutomaticallyOnly",
    "TaxCategory",
    "TaxCodeRequired",
    "CostElement",
    "CostElementCategory",
    "ControllingArea",
    "DefaultProfitCenter",
    "DefaultCostCenter",
    "HouseBank",
    "HouseBankAccount",
    "AccountManagedInExtSystem",
    "AuthorizationGroup",
    "MinorityInterestAccount",
    "PartnerCompany",
    "IsNonOperatingExpenseOrIncome",
    "IsProfitAndLossAccount",
]

I_GLACCOUNT_MIN_ROWS = 120_000
I_GLACCOUNT_DEFAULT_ROWS = 120_000
I_GLACCOUNT_MAX_ROWS = 150_000
I_GLACCOUNT_QUICK_TEST_ROWS = 600

_CHART_OF_ACCOUNTS = "INTL"


def _digits(rng: random.Random, n: int) -> str:
    return "".join(rng.choice(string.digits) for _ in range(n))


def _sample_date(rng: random.Random) -> str:
    start = datetime(2014, 1, 1)
    end = datetime(2026, 5, 1)
    day = start + timedelta(days=rng.randint(0, (end - start).days))
    return day.strftime("%Y%m%d")


def _first_digit(gl_account: str) -> str:
    for c in gl_account:
        if c.isdigit():
            return c
    return "3"


def _account_type(gl_account: str) -> tuple[str, str, str]:
    first = _first_digit(gl_account)
    if first in {"1", "2"}:
        return "S", "X", ""
    if first in {"3", "4"}:
        return "P", "", "X"
    if first in {"5", "6"}:
        return "P", "", "E"
    return "P", "", "N"


def _gl_group(gl_account: str) -> str:
    first = _first_digit(gl_account)
    mapping = {
        "1": "ASST",
        "2": "LIAB",
        "3": "REVN",
        "4": "REVN",
        "5": "EXPN",
        "6": "EXPN",
        "7": "COGS",
        "8": "OTHR",
        "9": "OTHR",
    }
    return mapping.get(first, "OTHR")


def _build_gl_number(base: str, idx: int) -> str:
    b = "".join(ch for ch in base if ch.isdigit()) or "300000"
    base_num = int(b[-6:])
    return str(base_num + (idx * 7) % 900000).zfill(6)[:10]


def _normalize_account_name(name: str) -> str:
    # Mantem estilo "limpo" como os outros CSVs (sem parenteses/virgulas de exemplo).
    s = re.sub(r"\([^)]*\)", " ", name or "")
    s = s.replace(",", " ").replace(";", " ").replace("/", " ")
    return " ".join(s.split()).strip()


def build_row(master: dict[str, str], client: str, idx: int, rng: random.Random) -> dict[str, str]:
    gl = _build_gl_number(master.get("GLAccount", ""), idx)
    seed_name = _normalize_account_name(master.get("GLAccountName", "Conta contabil"))
    name = f"{seed_name} {idx % 997:03d}"[:50]
    account_type, is_bs, pl_type = _account_type(gl)
    created = _sample_date(rng)
    changed = _sample_date(rng)
    is_pl = "X" if pl_type in {"X", "E", "N"} else ""

    return {
        "Client": client[:3],
        "ChartOfAccounts": _CHART_OF_ACCOUNTS,
        "GLAccount": gl,
        "GLAccountName": name[:30],
        "GLAccountLongName": name[:50],
        "AlternativeGLAccount": gl[-6:],
        "CountryChartOfAccounts": rng.choice(["", "BRPC", "USCX", "INTL"]),
        "AccountType": account_type,
        "GLAccountType": "N",
        "GLAccountGroup": _gl_group(gl),
        "IsBalanceSheetAccount": is_bs,
        "ProfitLossAccountType": pl_type,
        "RetainedEarningsAccount": "X" if is_bs == "X" and rng.random() < 0.08 else "",
        "CorporateGroupAccount": gl[-6:].rjust(6, "0"),
        "FunctionalArea": rng.choice(["YB01", "YB02", "YB10", ""]),
        "ConsolidationChartOfAccounts": rng.choice(["INTL", "GRP1", ""]),
        "ConsolidationAccount": gl[-6:] if rng.random() < 0.35 else "",
        "ExchangeRateType": rng.choice(["M", "B", "G", ""]),
        "TranslationDateType": rng.choice(["1", "2", ""]),
        "PlanningAccount": "X" if rng.random() < 0.3 else "",
        "AccountCurrency": rng.choice(["", "BRL", "USD", "EUR", "GBP"]),
        "CashFlowStatementAccount": f"CF{_digits(rng,4)}" if rng.random() < 0.3 else "",
        "CreatedByUser": rng.choice(["CB9980000010", "CB9980000011", "CB9980000012"]),
        "CreationDate": created,
        "LastChangedByUser": rng.choice(["CB9980000010", "CB9980000013", "CB9980000014"]),
        "LastChangeDate": changed,
        "AccountIsMarkedForDeletion": "X" if rng.random() < 0.03 else "",
        "IsBlockedForCreation": "X" if rng.random() < 0.04 else "",
        "IsBlockedForPosting": "X" if rng.random() < 0.05 else "",
        "IsBlockedForPlanning": "X" if rng.random() < 0.02 else "",
        "IsOpenItemManaged": "X" if is_bs == "X" and rng.random() < 0.35 else "",
        "IsLineItemDisplayed": "X" if rng.random() < 0.6 else "",
        "LineItemTaxDisplayOnly": "X" if rng.random() < 0.08 else "",
        "ReconciliationAccountIsReqd": "X" if is_bs == "X" and rng.random() < 0.15 else "",
        "ReconciliationAccountType": rng.choice(["D", "K", "A", ""]) if is_bs == "X" else "",
        "OpenItemClrngIsUsed": "X" if rng.random() < 0.25 else "",
        "SortKey": rng.choice(["001", "002", "003", "004", ""]),
        "FieldStatusGroup": rng.choice(["G001", "Y001", "Y010", ""]),
        "PostAutomaticallyOnly": "X" if rng.random() < 0.08 else "",
        "TaxCategory": rng.choice(["*", "+", "-", ""]) if pl_type in {"X", "E"} else "",
        "TaxCodeRequired": "X" if pl_type in {"X", "E"} and rng.random() < 0.2 else "",
        "CostElement": gl if rng.random() < 0.5 else "",
        "CostElementCategory": rng.choice(["1", "11", "12", "90", ""]) if rng.random() < 0.55 else "",
        "ControllingArea": rng.choice(["0001", "A000", ""]),
        "DefaultProfitCenter": rng.choice(["PC-1000", "PC-2000", "PC-3000", ""]),
        "DefaultCostCenter": rng.choice(["CC1000", "CC2000", "CC3000", ""]),
        "HouseBank": rng.choice(["HB01", "HB02", ""]) if rng.random() < 0.15 else "",
        "HouseBankAccount": rng.choice(["ACC01", "ACC02", ""]) if rng.random() < 0.15 else "",
        "AccountManagedInExtSystem": "X" if rng.random() < 0.03 else "",
        "AuthorizationGroup": rng.choice(["F01", "F02", "F03", ""]),
        "MinorityInterestAccount": "X" if rng.random() < 0.01 else "",
        "PartnerCompany": rng.choice(["BR01", "US10", "DE10", "FR01", "UK01", ""]),
        "IsNonOperatingExpenseOrIncome": "X" if pl_type == "N" and rng.random() < 0.4 else "",
        "IsProfitAndLossAccount": is_pl,
    }


def main() -> None:
    repo = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Gera CSV sintetico tipo I_GLAccount.")
    parser.add_argument("--output", type=Path, default=repo / "data" / "I_GLAccount.csv")
    parser.add_argument(
        "--rows",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Linhas sem header (opcional). Fora de --quick: ajustado ao intervalo "
            f"[{I_GLACCOUNT_MIN_ROWS}, {I_GLACCOUNT_MAX_ROWS}]; sem este argumento usa {I_GLACCOUNT_DEFAULT_ROWS}."
        ),
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help=f"Teste rapido: gera exatamente {I_GLACCOUNT_QUICK_TEST_ROWS} linhas.",
    )
    parser.add_argument("--seed", type=int, default=SYNTHETIC_MASTER_SEED)
    parser.add_argument(
        "--client",
        type=str,
        default="",
        help="Mandante fixo (3 chars). Vazio = um dos MASTER_CLIENT_IDS por linha, rotativo.",
    )
    args = parser.parse_args()

    if args.quick:
        if args.rows is not None:
            print("Aviso: --quick ignora --rows (usa volume de teste fixo).", file=sys.stderr)
        args.rows = I_GLACCOUNT_QUICK_TEST_ROWS
    else:
        requested = args.rows if args.rows is not None else I_GLACCOUNT_DEFAULT_ROWS
        if requested < I_GLACCOUNT_MIN_ROWS:
            print(
                f"Aviso: --rows={requested} abaixo do minimo; ajustado a {I_GLACCOUNT_MIN_ROWS}.",
                file=sys.stderr,
            )
        if requested > I_GLACCOUNT_MAX_ROWS:
            print(
                f"Aviso: --rows={requested} acima do maximo; ajustado a {I_GLACCOUNT_MAX_ROWS}.",
                file=sys.stderr,
            )
        args.rows = max(I_GLACCOUNT_MIN_ROWS, min(requested, I_GLACCOUNT_MAX_ROWS))

    rng = random.Random(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for i in range(args.rows):
        m = MASTER_GL_ACCOUNTS[i % len(MASTER_GL_ACCOUNTS)]
        client = args.client.strip()[:3] if args.client else MASTER_CLIENT_IDS[i % len(MASTER_CLIENT_IDS)]
        rows.append(build_row(m, client, i, rng))

    out_cols = [c for c in GLACCOUNT_COLUMNS if any(csv_cell_has_semantic_value(r.get(c)) for r in rows)]
    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_cols)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in out_cols})

    print(f"Escrito {args.rows} linhas ({len(out_cols)} colunas) em {args.output.resolve()}")


if __name__ == "__main__":
    main()
