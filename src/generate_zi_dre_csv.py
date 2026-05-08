"""
CSV sintetico da interface ZI_DRE para consumo no SAC.

Fonte principal:
- data/I_CompanyCode.csv
- data/I_Customer.csv
- data/I_GLAccount.csv
- data/I_CostCenter.csv
- data/I_ProfitCenter.csv
- data/I_Product.csv

Regras:
- Mantem os mesmos campos da CDS `ZI_DRE`.
- Valores sao ficticios, mas coerentes com as dimensoes.
- Remove apenas colunas 100% vazias em todas as linhas.
- Fora de --quick, ajusta volume para faixa 120k-150k.
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from datetime import date, timedelta
from pathlib import Path

from sap_synthetic_masters import (
    SYNTHETIC_MASTER_SEED,
    csv_cell_has_semantic_value,
)

ZI_DRE_MIN_ROWS = 120_000
ZI_DRE_DEFAULT_ROWS = 120_000
ZI_DRE_MAX_ROWS = 150_000
ZI_DRE_QUICK_TEST_ROWS = 600

ZI_DRE_COLUMNS = [
    "CompanyCode",
    "CompanyCodeName",
    "Ledger",
    "DocumentNumber",
    "DocumentItem",
    "FiscalYear",
    "FiscalPeriod",
    "PostingDate",
    "DocumentDate",
    "ChartOfAccounts",
    "GLAccount",
    "GLAccountName",
    "Customer",
    "CustomerName",
    "GLAccountType",
    "GLAccountTypeName",
    "GLAccountGroup",
    "GLAccountGroupName",
    "ControllingArea",
    "CostCenter",
    "CostCenterName",
    "ProfitCenter",
    "ProfitCenterName",
    "FunctionalArea",
    "FunctionalAreaName",
    "Segment",
    "SegmentName",
    "Branch",
    "Plant",
    "PlantName",
    "DocType",
    "ItemText",
    "RefDocType",
    "Currency",
    "DebitCreditCode",
    "AmountInCompanyCurrency",
    "ValorReceita",
    "ValorDeducoes",
    "ValorDespesa",
    "ValorLiquido",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo nao encontrado: {path}")
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _sample_date(rng: random.Random) -> date:
    start = date(2023, 1, 1)
    end = date(2026, 4, 30)
    return start + timedelta(days=rng.randint(0, (end - start).days))


def _fiscal_period(d: date) -> str:
    return f"{d.year}{d.month:02d}"


def _gl_type_name(gl_type: str) -> str:
    return {
        "N": "Nonoperating Expense or Income",
        "P": "Primary Costs or Revenue",
        "X": "Balance Sheet Account",
        "S": "Secondary Costs",
    }.get(gl_type or "", "")


def _gl_group_name(group: str) -> str:
    return {
        "BAL": "Balanco",
        "MAT": "Materiais",
        "REV": "Receita",
        "EXP": "Despesa",
        "ROOT": "Estrutura",
    }.get(group or "", "")


def _build_rows(
    n_rows: int,
    companies: list[dict[str, str]],
    customers: list[dict[str, str]],
    gl_accounts: list[dict[str, str]],
    cost_centers: list[dict[str, str]],
    profit_centers: list[dict[str, str]],
    products: list[dict[str, str]],
    rng: random.Random,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    gl_final_accounts = [g for g in gl_accounts if (g.get("GLAccount", "").isdigit() and len(g.get("GLAccount", "")) == 6)]
    if not companies or not customers or not gl_final_accounts:
        return rows

    company_to_currency: dict[str, str] = {
        c.get("CompanyCode", ""): c.get("Currency", "")
        for c in companies
        if c.get("CompanyCode")
    }
    company_to_controlling_area: dict[str, str] = {
        c.get("CompanyCode", ""): c.get("ControllingArea", "")
        for c in companies
        if c.get("CompanyCode")
    }
    plant_to_name: dict[str, str] = {}
    for p in products:
        plant = p.get("Plant", "")
        if plant and plant not in plant_to_name and p.get("ProductDescription", ""):
            plant_to_name[plant] = p.get("ProductDescription", "")

    for i in range(n_rows):
        c = companies[i % len(companies)]
        cust = customers[rng.randrange(len(customers))]
        gl = gl_final_accounts[rng.randrange(len(gl_final_accounts))]
        cc = cost_centers[rng.randrange(len(cost_centers))] if cost_centers else {}
        pc = profit_centers[rng.randrange(len(profit_centers))] if profit_centers else {}

        posting = _sample_date(rng)
        doc_date = posting - timedelta(days=rng.randint(0, 6))
        fiscal_year = str(posting.year)
        fiscal_period = _fiscal_period(posting)
        amount = round(rng.uniform(250.0, 45000.0), 2)

        gl_group = gl.get("GLAccountGroup", "")
        debit_credit = rng.choice(["S", "H"])
        signed_amount = amount if debit_credit == "S" else -amount

        valor_receita = 0.0
        valor_deducoes = 0.0
        valor_despesa = 0.0
        if gl_group == "REV":
            # Receita na DRE normalmente aparece negativa em lancamento contabil.
            valor_receita = -abs(signed_amount)
        elif gl_group == "EXP":
            valor_despesa = abs(signed_amount)
        elif gl_group == "MAT":
            valor_despesa = abs(signed_amount)
        else:
            valor_deducoes = abs(signed_amount) if signed_amount < 0 else 0.0
        valor_liquido = valor_receita - valor_deducoes - valor_despesa

        plant_code = rng.choice(["P001", "P002", "P003", "P004"])
        plant_name = {
            "P001": "Fabrica Matriz SP",
            "P002": "Centro Distribuicao RJ",
            "P003": "Planta Exportacao SC",
            "P004": "Filial Norte",
        }.get(plant_code, "")
        if plant_code in plant_to_name and plant_to_name[plant_code]:
            plant_name = plant_to_name[plant_code][:35]

        cost_center_code = cc.get("CostCenter", "") if cc else ""
        cost_center_name = cc.get("CostCenterName", "") if cc else ""
        profit_center_code = pc.get("ProfitCenter", "") if pc else ""
        profit_center_name = pc.get("ProfitCenterName", "") if pc else ""
        controlling_area = (
            cc.get("ControllingArea", "")
            or pc.get("ControllingArea", "")
            or company_to_controlling_area.get(c.get("CompanyCode", ""), "")
            or "0001"
        )

        rows.append(
            {
                "CompanyCode": c.get("CompanyCode", ""),
                "CompanyCodeName": c.get("CompanyCodeName", ""),
                "Ledger": "0L",
                "DocumentNumber": str(1900000000 + i).zfill(10),
                "DocumentItem": str((i % 999) + 1).zfill(3),
                "FiscalYear": fiscal_year,
                "FiscalPeriod": fiscal_period,
                "PostingDate": posting.strftime("%Y%m%d"),
                "DocumentDate": doc_date.strftime("%Y%m%d"),
                "ChartOfAccounts": gl.get("ChartOfAccounts", "YCOA"),
                "GLAccount": gl.get("GLAccount", ""),
                "GLAccountName": gl.get("GLAccountName", ""),
                "Customer": cust.get("Customer", ""),
                "CustomerName": cust.get("CustomerName", ""),
                "GLAccountType": gl.get("GLAccountType", ""),
                "GLAccountTypeName": _gl_type_name(gl.get("GLAccountType", "")),
                "GLAccountGroup": gl_group,
                "GLAccountGroupName": _gl_group_name(gl_group),
                "ControllingArea": controlling_area,
                "CostCenter": cost_center_code,
                "CostCenterName": cost_center_name,
                "ProfitCenter": profit_center_code,
                "ProfitCenterName": profit_center_name,
                "FunctionalArea": rng.choice(["YB01", "YB02", "YB10", ""]),
                "FunctionalAreaName": rng.choice(
                    [
                        "Administracao",
                        "Comercial",
                        "Operacoes",
                        "",
                    ]
                ),
                "Segment": rng.choice(["SEG_A", "SEG_B", "SEG_C", ""]),
                "SegmentName": rng.choice(["Consumo", "Industrial", "Servicos", ""]),
                "Branch": rng.choice(["BR01", "SP01", "RJ01", ""]),
                "Plant": plant_code,
                "PlantName": plant_name,
                "DocType": rng.choice(["SA", "KR", "RV", "AB"]),
                "ItemText": rng.choice(
                    [
                        "Lancamento contabil sintetico",
                        "Ajuste DRE mensal",
                        "Receita operacional",
                        "Despesa administrativa",
                    ]
                ),
                "RefDocType": rng.choice(["BKPF", "VBRK", "MKPF", ""]),
                "Currency": company_to_currency.get(c.get("CompanyCode", ""), c.get("Currency", "BRL")),
                "DebitCreditCode": debit_credit,
                "AmountInCompanyCurrency": f"{signed_amount:.2f}",
                "ValorReceita": f"{valor_receita:.2f}",
                "ValorDeducoes": f"{valor_deducoes:.2f}",
                "ValorDespesa": f"{valor_despesa:.2f}",
                "ValorLiquido": f"{valor_liquido:.2f}",
            }
        )
    return rows


def main() -> None:
    repo = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Gera ZI_DRE.csv para consumo no SAC.")
    parser.add_argument("--output", type=Path, default=repo / "data" / "ZI_DRE.csv")
    parser.add_argument("--companycode-csv", type=Path, default=repo / "data" / "I_CompanyCode.csv")
    parser.add_argument("--customer-csv", type=Path, default=repo / "data" / "I_Customer.csv")
    parser.add_argument("--glaccount-csv", type=Path, default=repo / "data" / "I_GLAccount.csv")
    parser.add_argument("--costcenter-csv", type=Path, default=repo / "data" / "I_CostCenter.csv")
    parser.add_argument("--profitcenter-csv", type=Path, default=repo / "data" / "I_ProfitCenter.csv")
    parser.add_argument("--product-csv", type=Path, default=repo / "data" / "I_Product.csv")
    parser.add_argument("--seed", type=int, default=SYNTHETIC_MASTER_SEED)
    parser.add_argument("--rows", type=int, default=None, metavar="N")
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    if args.quick:
        if args.rows is not None:
            print("Aviso: --quick ignora --rows (usa volume de teste fixo).", file=sys.stderr)
        n_rows = ZI_DRE_QUICK_TEST_ROWS
    else:
        requested = args.rows if args.rows is not None else ZI_DRE_DEFAULT_ROWS
        if requested < ZI_DRE_MIN_ROWS:
            print(
                f"Aviso: --rows={requested} abaixo do minimo; ajustado a {ZI_DRE_MIN_ROWS}.",
                file=sys.stderr,
            )
        if requested > ZI_DRE_MAX_ROWS:
            print(
                f"Aviso: --rows={requested} acima do maximo; ajustado a {ZI_DRE_MAX_ROWS}.",
                file=sys.stderr,
            )
        n_rows = max(ZI_DRE_MIN_ROWS, min(requested, ZI_DRE_MAX_ROWS))

    rng = random.Random(args.seed)
    companies = _read_csv(args.companycode_csv)
    customers = _read_csv(args.customer_csv)
    gl_accounts = _read_csv(args.glaccount_csv)
    cost_centers = _read_csv(args.costcenter_csv)
    profit_centers = _read_csv(args.profitcenter_csv)
    products = _read_csv(args.product_csv)

    rows = _build_rows(
        n_rows,
        companies,
        customers,
        gl_accounts,
        cost_centers,
        profit_centers,
        products,
        rng,
    )
    out_cols = [c for c in ZI_DRE_COLUMNS if any(csv_cell_has_semantic_value(r.get(c)) for r in rows)]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_cols)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in out_cols})

    print(f"Escrito {len(rows)} linhas ({len(out_cols)} colunas) em {args.output.resolve()}")


if __name__ == "__main__":
    main()
