"""
CSV sintetico espelho da view standard `I_CostCenter` (dimensao CO / OData A_CostCenterType).

Elementos alinhados ao VDM CostCenter + textos usuais (CostCenterName, CostCenterDescription)
como em exposicoes CDS tipicas. Primeira coluna `Client`, como nos demais CSVs deste repo.

- Colunas em que **todas** as linhas ficam vazias sao omitidas do CSV final.
- Fora de --quick: volume forcado ao intervalo 120k-150k (com aviso se --rows estiver fora).

Uso:
  python src/generate_i_costcenter_csv.py [--rows N] --output data/I_CostCenter.csv
"""

from __future__ import annotations

import argparse
import csv
import random
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

from sap_synthetic_masters import (
    I_COSTCENTER_DEFAULT_ROWS,
    I_COSTCENTER_MAX_ROWS,
    I_COSTCENTER_MIN_ROWS,
    I_COSTCENTER_QUICK_TEST_ROWS,
    MASTER_CLIENT_IDS,
    MASTER_COMPANY_CODES,
    MASTER_CONTROLLING_AREAS,
    MASTER_PLANT_NAMES,
    MASTER_PROFIT_CENTERS,
    SYNTHETIC_MASTER_SEED,
    csv_cell_has_semantic_value,
)

_COMPANY_LANG2: dict[str, str] = {
    "BR01": "PT",
    "US10": "EN",
    "DE10": "DE",
    "FR01": "FR",
    "UK01": "EN",
}

_COMPANY_COUNTRY: dict[str, str] = {
    "BR01": "BR",
    "US10": "US",
    "DE10": "DE",
    "FR01": "FR",
    "UK01": "GB",
}

# Hierarquia / categorias CO com cara de producao/projeto/admin — letras KOART-tipicas curtas.
_CC_CATEGORIES: tuple[str, ...] = ("F", "V", "W", "A", "S", "D", "C")
_CC_AREA_NAMES: tuple[str, ...] = (
    "Operacoes Industriais",
    "Manutencao Fabril",
    "Planejamento Producao",
    "Logistica Interna",
    "Qualidade Industrial",
    "Engenharia Processos",
    "Suprimentos Estrategicos",
    "Controladoria Operacional",
    "Tecnologia Industrial",
    "Administracao Corporativa",
)
_CC_AREA_NAMES_SHORT: tuple[str, ...] = (
    "Operacoes Ind.",
    "Manutencao",
    "Planejamento",
    "Logistica",
    "Qualidade",
    "Engenharia",
    "Suprimentos",
    "Controladoria",
    "Tecnologia",
    "Administracao",
)

_COSTCENTER_COLUMNS: list[str] = [
    "Client",
    "ControllingArea",
    "CostCenter",
    "ValidityEndDate",
    "ValidityStartDate",
    "CompanyCode",
    "CostCenterName",
    "CostCenterDescription",
    "Language",
    "ProfitCenter",
    "FunctionalArea",
    "BusinessArea",
    "Department",
    "CostCenterCategory",
    "Country",
    "Region",
    "CityName",
    "CostCenterCurrency",
    "CostCenterCreationDate",
    "CostCenterCreatedByUser",
    "CostCtrResponsibleUser",
    "CostCtrResponsiblePersonName",
    "CostCenterStandardHierArea",
    "ConsumptionQtyIsRecorded",
    "CostingSheet",
    "IsBlkdForPrimaryCostsPosting",
    "IsBlkdForSecondaryCostsPosting",
    "IsBlockedForRevenuePosting",
    "IsBlockedForCommitmentPosting",
    "IsBlockedForPlanPrimaryCosts",
    "IsBlockedForPlanRevenues",
    "IsBlockedForPlanSecondaryCosts",
]


def _pad(s: str | None, max_len: int) -> str:
    if s is None:
        return ""
    return (str(s))[:max_len]


def _normalize_text(s: str) -> str:
    t = re.sub(r"\([^)]*\)", " ", s or "")
    t = t.replace(",", " ").replace(";", " ").replace("/", " ")
    return " ".join(t.split()).strip()


def _sample_date_between(rng: random.Random, start: datetime, end: datetime) -> str:
    day = start + timedelta(days=rng.randint(0, max(0, (end - start).days)))
    return day.strftime("%Y%m%d")


def _cost_center_kostl(idx: int) -> str:
    base = 1_000_000 + (idx * 13) % 8_900_000
    return str(base).zfill(10)[:10]


def build_row(
    company: dict[str, str],
    controlling_area: str,
    client: str,
    idx: int,
    rng: random.Random,
) -> dict[str, str]:
    bukrs = company["CompanyCode"]
    waers = company.get("CompanyCodeCurrency", "EUR")
    country = _COMPANY_COUNTRY.get(bukrs, "US")
    lang2 = _COMPANY_LANG2.get(bukrs, "EN")
    locales = {"BR": "pt_BR", "US": "en_US", "DE": "de_DE", "FR": "fr_FR", "GB": "en_GB"}
    fk = Faker(locales.get(country, "en_US"))
    fk.seed_instance(int(rng.getrandbits(32)) ^ SYNTHETIC_MASTER_SEED ^ (idx * 17))

    kostl = _cost_center_kostl(idx)
    profit_seed = MASTER_PROFIT_CENTERS[idx % len(MASTER_PROFIT_CENTERS)]
    profit_digits = "".join(ch for ch in profit_seed if ch.isdigit()) or "1000"
    profit = profit_digits.zfill(10)[:10]
    plant_code = list(MASTER_PLANT_NAMES.keys())[idx % len(MASTER_PLANT_NAMES)]
    plant_label = _normalize_text(MASTER_PLANT_NAMES.get(plant_code, plant_code))[:30]

    area_name = _CC_AREA_NAMES[idx % len(_CC_AREA_NAMES)]
    area_short = _CC_AREA_NAMES_SHORT[idx % len(_CC_AREA_NAMES_SHORT)]
    short = _pad(_normalize_text(f"{area_short} {plant_code}"), 20)
    long = _pad(_normalize_text(f"{area_name} - {plant_label}")[:40], 40)

    created = _sample_date_between(rng, datetime(2015, 1, 1), datetime(2026, 4, 1))
    valid_from = _sample_date_between(rng, datetime(2016, 1, 1), datetime(2021, 6, 1))
    xf = rng.choice(["", "", "X"])

    user_cb = rng.choice(["CB9980001010", "CB9980001020", "CB9980001030"])
    resp_user = _pad(rng.choice(["CO_MANAGER1", "CO_ANALYST1", "CO_COORD01", "CO_SUPERV1"]), 12)
    person = _pad(fk.last_name().upper()[:1] + fk.first_name()[:18], 20)

    business_area = rng.choice(["1000", "2000", "3000", ""])
    func_area = rng.choice(["YB01", "YB02", "YB10", "YB20", ""])
    dept = _pad(_normalize_text(area_name.replace(" ", ""))[:12], 12)
    hier = _pad(f"STD-{controlling_area}", 12)
    if country == "US":
        region = rng.choice(["CA", "TX", "NY", "FL", "IL", "WA", ""])
    elif country == "BR":
        region = rng.choice(["SP", "RJ", "PR", "SC", "MG", "BA", ""])
    elif country == "DE":
        region = rng.choice(["BW", "BY", "NW", "HE", "RP", ""])
    elif country == "FR":
        region = rng.choice(["IDF", "ARA", "NAQ", "OCC", ""])
    elif country == "GB":
        region = rng.choice(["ENG", "SCT", "WLS", "NIR", ""])
    else:
        region = ""

    return {
        "Client": _pad(client, 3),
        "ControllingArea": _pad(controlling_area, 4),
        "CostCenter": _pad(kostl, 10),
        "ValidityEndDate": "99991231",
        "ValidityStartDate": valid_from,
        "CompanyCode": _pad(bukrs, 4),
        "CostCenterName": _pad(short, 20),
        "CostCenterDescription": _pad(long, 40),
        "Language": _pad(lang2, 2),
        "ProfitCenter": _pad(profit, 10),
        "FunctionalArea": _pad(func_area, 16),
        "BusinessArea": _pad(business_area, 4),
        "Department": _pad(dept, 12),
        "CostCenterCategory": _pad(rng.choice(_CC_CATEGORIES), 1),
        "Country": _pad(country, 3),
        "Region": _pad(region, 3),
        "CityName": _pad(fk.city()[:35], 35),
        "CostCenterCurrency": _pad(waers, 5),
        "CostCenterCreationDate": created,
        "CostCenterCreatedByUser": _pad(user_cb, 12),
        "CostCtrResponsibleUser": _pad(resp_user, 12),
        "CostCtrResponsiblePersonName": _pad(person, 20),
        "CostCenterStandardHierArea": _pad(hier, 12),
        "ConsumptionQtyIsRecorded": xf if rng.random() < 0.18 else "",
        "CostingSheet": _pad(rng.choice(["", "CS01", "CS02", "ZCST1"]) if rng.random() > 0.55 else "", 6),
        "IsBlkdForPrimaryCostsPosting": xf if rng.random() < 0.04 else "",
        "IsBlkdForSecondaryCostsPosting": xf if rng.random() < 0.03 else "",
        "IsBlockedForRevenuePosting": xf if rng.random() < 0.06 else "",
        "IsBlockedForCommitmentPosting": xf if rng.random() < 0.05 else "",
        "IsBlockedForPlanPrimaryCosts": xf if rng.random() < 0.04 else "",
        "IsBlockedForPlanRevenues": xf if rng.random() < 0.05 else "",
        "IsBlockedForPlanSecondaryCosts": xf if rng.random() < 0.04 else "",
    }


def main() -> None:
    repo = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Gera CSV sintetico tipo I_CostCenter.")
    parser.add_argument("--output", type=Path, default=repo / "data" / "I_CostCenter.csv")
    parser.add_argument(
        "--rows",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Linhas sem header (opcional). Fora de --quick: ajustado ao intervalo "
            f"[{I_COSTCENTER_MIN_ROWS}, {I_COSTCENTER_MAX_ROWS}]; sem este argumento usa {I_COSTCENTER_DEFAULT_ROWS}."
        ),
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help=f"Teste rapido: gera exatamente {I_COSTCENTER_QUICK_TEST_ROWS} linhas.",
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
        args.rows = I_COSTCENTER_QUICK_TEST_ROWS
    else:
        requested = args.rows if args.rows is not None else I_COSTCENTER_DEFAULT_ROWS
        if requested < I_COSTCENTER_MIN_ROWS:
            print(
                f"Aviso: --rows={requested} abaixo do minimo; ajustado a {I_COSTCENTER_MIN_ROWS}.",
                file=sys.stderr,
            )
        if requested > I_COSTCENTER_MAX_ROWS:
            print(
                f"Aviso: --rows={requested} acima do maximo; ajustado a {I_COSTCENTER_MAX_ROWS}.",
                file=sys.stderr,
            )
        args.rows = max(I_COSTCENTER_MIN_ROWS, min(requested, I_COSTCENTER_MAX_ROWS))

    rng = random.Random(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for i in range(args.rows):
        co = MASTER_COMPANY_CODES[i % len(MASTER_COMPANY_CODES)]
        kokrs = MASTER_CONTROLLING_AREAS[i % len(MASTER_CONTROLLING_AREAS)]
        client = args.client.strip()[:3] if args.client else MASTER_CLIENT_IDS[i % len(MASTER_CLIENT_IDS)]
        rows.append(build_row(co, kokrs, client, i, rng))

    out_cols = [c for c in _COSTCENTER_COLUMNS if any(csv_cell_has_semantic_value(r.get(c)) for r in rows)]
    with args.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in out_cols})

    print(f"Escrito {args.rows} linhas ({len(out_cols)} colunas) em {args.output.resolve()}")


if __name__ == "__main__":
    main()
