"""
CSV sintetico I_CompanyCode: mesma lista/ordem de elementos que o OData VDM
SAP expoe para o tipo empresarial A_CompanyCodeType (consulta aos fluent fields
SAP Cloud SDK s4hana-api-odata, servico API COMPANYCODE / CDS I_CompanyCode).

Prefixo obrigatorio Mandt: primeira coluna `Client`, alinhada a I_Customer / I_Supplier.

Somente valores sao sinteticos; codigos empresa/moeda vêm de `sap_synthetic_masters.MASTER_COMPANY_CODES`.
Colunas em que **todas** as linhas ficarem vazias nao sao gravadas no CSV (mantem-se se houver pelo menos um valor).

Uso:
  python src/generate_i_companycode_csv.py --output data/I_CompanyCode.csv
"""

from __future__ import annotations

import argparse
import csv
import random
import string
from pathlib import Path

from faker import Faker

from sap_synthetic_masters import (
    MASTER_CLIENT_IDS,
    MASTER_COMPANY_CODES,
    SYNTHETIC_MASTER_SEED,
    column_order_excluding_always_empty,
)

# Ordem = sequencia de propriedades no builder SAP Cloud SDK CompanyCode (A_CompanyCodeType) + Client no inicio.
COMPANYCODE_COLUMNS = [
    "Client",
    "CompanyCode",
    "CompanyCodeName",
    "CityName",
    "Country",
    "Currency",
    "Language",
    "ChartOfAccounts",
    "FiscalYearVariant",
    "Company",
    "CreditControlArea",
    "CountryChartOfAccounts",
    "FinancialManagementArea",
    "AddressId",
    "TaxableEntity",
    "VatRegistration",
    "ExtendedWhldgTaxIsActive",
    "ControllingArea",
    "FieldStatusVariant",
    "NonTaxableTransactionTaxCode",
    "DocDateIsUsedForTaxDetn",
    "TaxRptgDateIsActive",
]

# Regiao/pais / idioma coerentes com codigo empresa do lab.
_COMPANY_TO_COUNTRY_LANG: dict[str, tuple[str, str]] = {
    "BR01": ("BR", "P"),
    "US10": ("US", "E"),
    "DE10": ("DE", "D"),
    "FR01": ("FR", "F"),
    "UK01": ("GB", "E"),
}

# Plano de contas / variantes ficticias mas estaveis por empresa.
_CHART_FISCAL: dict[str, tuple[str, str]] = {
    "BR01": ("BRPC", "Y1BR"),
    "US10": ("USCX", "K4US"),
    "DE10": ("INTL", "K4DE"),
    "FR01": ("FRNL", "K4FR"),
    "UK01": ("UKPL", "K4UK"),
}


def _digits(rng: random.Random, n: int) -> str:
    return "".join(rng.choice(string.digits) for _ in range(n))


def _pad(s: str, n: int) -> str:
    return (s or "")[:n]


def _city_sample(fk_local: Faker) -> str:
    return fk_local.city()[:35]


def build_row(master: dict[str, str], client: str, rng: random.Random) -> dict[str, str]:
    bukrs = master["CompanyCode"]
    fname = master.get("CompanyName", bukrs)[:25]
    cc = master.get("CompanyCodeCurrency", "EUR")
    country, lang = _COMPANY_TO_COUNTRY_LANG.get(bukrs, ("US", "E"))
    chart, fyear = _CHART_FISCAL.get(bukrs, ("INTL", "K4"))

    locales = {"BR": "pt_BR", "US": "en_US", "DE": "de_DE", "FR": "fr_FR", "GB": "en_GB"}
    fk = Faker(locales.get(country, "en_US"))
    fk.seed_instance(int(rng.getrandbits(32)) ^ SYNTHETIC_MASTER_SEED ^ hash(bukrs) % (2**31))

    company_id = "".join(ch for ch in bukrs if ch.isalnum()).upper()[:6].ljust(6, "0")
    adr = _digits(rng, 10)

    vatreg = ""
    if country == "DE":
        vatreg = f"DE{_digits(rng, 9)}"
    elif country == "BR":
        vatreg = _digits(rng, 14)
    elif country == "GB":
        vatreg = f"GB{_digits(rng, 9)}"

    xf = rng.choice(["", "", "X"])

    return {
        "Client": _pad(client, 3),
        "CompanyCode": _pad(bukrs, 4),
        "CompanyCodeName": _pad(fname, 25),
        "CityName": _pad(_city_sample(fk), 35),
        "Country": _pad(country, 3),
        "Currency": _pad(cc, 5),
        "Language": _pad(lang, 1),
        "ChartOfAccounts": _pad(chart, 4),
        "FiscalYearVariant": _pad(fyear, 2),
        "Company": _pad(company_id, 6),
        "CreditControlArea": _pad(rng.choice(["0001", "0002", "Z001"]), 4),
        "CountryChartOfAccounts": _pad(chart if rng.random() > 0.35 else "", 4),
        "FinancialManagementArea": _pad(rng.choice(["", "0001", "ZFI1"]), 4),
        "AddressId": _pad(adr, 10),
        "TaxableEntity": _pad("" if rng.random() > 0.4 else f"TX{_digits(rng, 6)}", 16),
        "VatRegistration": _pad(vatreg, 20),
        "ExtendedWhldgTaxIsActive": xf if rng.random() < 0.15 else "",
        "ControllingArea": _pad(rng.choice(["0001", "", "CCA1"]), 4),
        "FieldStatusVariant": _pad(rng.choice(["", "Y001", "G001"]), 6),
        "NonTaxableTransactionTaxCode": _pad("" if rng.random() > 0.3 else rng.choice(["V0", "VX"]), 4),
        "DocDateIsUsedForTaxDetn": xf if rng.random() < 0.12 else "",
        "TaxRptgDateIsActive": xf if rng.random() < 0.12 else "",
    }


def main() -> None:
    repo = Path(__file__).resolve().parent.parent
    p = argparse.ArgumentParser(description="Gera I_CompanyCode.csv a partir dos mestres.")
    p.add_argument("--output", type=Path, default=repo / "data" / "I_CompanyCode.csv")
    p.add_argument("--seed", type=int, default=SYNTHETIC_MASTER_SEED)
    p.add_argument(
        "--client",
        type=str,
        default="",
        help="Mandante fixo (3 chars). Vazio = um dos MASTER_CLIENT_IDS por linha, rotativo.",
    )
    args = p.parse_args()

    rng = random.Random(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for i, m in enumerate(MASTER_COMPANY_CODES):
        cl = args.client.strip()[:3] if args.client else MASTER_CLIENT_IDS[i % len(MASTER_CLIENT_IDS)]
        rows.append(build_row(m, cl, rng))

    out_cols = column_order_excluding_always_empty(COMPANYCODE_COLUMNS, rows)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in out_cols})

    print(f"Escrito {len(rows)} linhas ({len(out_cols)} colunas) em {args.output.resolve()}")


if __name__ == "__main__":
    main()
