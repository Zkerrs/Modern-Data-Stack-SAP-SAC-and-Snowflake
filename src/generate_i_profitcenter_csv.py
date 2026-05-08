"""
CSV sintetico espelho da view standard `I_ProfitCenter` (CO-PA-O / OData A_ProfitCenterType).

Inclui textos usuarios `ProfitCenterName` e `ProfitCenterLongName` (A_ProfitCenterTextType),
com `Client` no inicio alinhado aos demais CSVs deste repo.

- Colunas 100 por cento vazias em todas as linhas sao omitidas do CSV final.
- Fora de --quick: volume forcado ao intervalo 120k-150k (ajuste automatico + aviso).

Uso:
  python src/generate_i_profitcenter_csv.py [--rows N] --output data/I_ProfitCenter.csv
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
    I_PROFITCENTER_DEFAULT_ROWS,
    I_PROFITCENTER_MAX_ROWS,
    I_PROFITCENTER_MIN_ROWS,
    I_PROFITCENTER_QUICK_TEST_ROWS,
    MASTER_CLIENT_IDS,
    MASTER_COMPANY_CODES,
    MASTER_CONTROLLING_AREAS,
    MASTER_PLANT_NAMES,
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

_SEGMENTS: tuple[str, ...] = ("CORP01", "SEGM_RETBL", "SEGM_WOLS", "SVC_GRP01", "")
_PC_AREA_NAMES: tuple[str, ...] = (
    "Unidade Bens Consumo",
    "Unidade Solucoes Industriais",
    "Unidade Embalagens",
    "Unidade Distribuicao",
    "Unidade Servicos Tecnicos",
    "Unidade Metalurgia",
    "Unidade Materiais Especiais",
    "Unidade Engenharia Aplicada",
    "Unidade Pos-Venda",
    "Unidade Exportacao",
)
_PC_AREA_NAMES_SHORT: tuple[str, ...] = (
    "Bens Consumo",
    "Solucoes Ind.",
    "Embalagens",
    "Distribuicao",
    "Servicos Tec.",
    "Metalurgia",
    "Materiais Esp.",
    "Engenharia Apl.",
    "Pos-Venda",
    "Exportacao",
)

_PROFITCENTER_COLUMNS: list[str] = [
    "Client",
    "ControllingArea",
    "ProfitCenter",
    "ValidityEndDate",
    "ValidityStartDate",
    "CompanyCode",
    "ProfitCenterName",
    "ProfitCenterLongName",
    "Language",
    "AdditionalName",
    "AddressName",
    "CityName",
    "Country",
    "DataCommunicationPhoneNumber",
    "Department",
    "District",
    "FaxNumber",
    "FormOfAddress",
    "FormulaPlanningTemplate",
    "PhoneNumber1",
    "PhoneNumber2",
    "POBox",
    "PostalCode",
    "ProfitCenterAddrName3",
    "ProfitCenterAddrName4",
    "ProfitCenterCreatedByUser",
    "ProfitCenterCreationDate",
    "ProfitCenterIsBlocked",
    "ProfitCenterPrinterName",
    "ProfitCenterStandardHierarchy",
    "ProfitCtrResponsiblePersonName",
    "ProfitCtrResponsibleUser",
    "Region",
    "Segment",
    "StreetAddressName",
    "TaxJurisdiction",
    "TeleboxNumber",
    "TelexNumber",
]


def _pad(s: str | None, max_len: int) -> str:
    if s is None:
        return ""
    return str(s)[:max_len]


def _normalize_text(s: str) -> str:
    t = re.sub(r"\([^)]*\)", " ", s or "")
    t = t.replace(",", " ").replace(";", " ").replace("/", " ")
    return " ".join(t.split()).strip()


def _sample_date_between(rng: random.Random, start: datetime, end: datetime) -> str:
    day = start + timedelta(days=rng.randint(0, max(0, (end - start).days)))
    return day.strftime("%Y%m%d")


def _region_for_country(country: str, rng: random.Random) -> str:
    if country == "US":
        return rng.choice(["CA", "TX", "NY", "FL", "IL", "WA", ""])
    if country == "BR":
        return rng.choice(["SP", "RJ", "PR", "SC", "MG", "BA", ""])
    if country == "DE":
        return rng.choice(["BW", "BY", "NW", "HE", "RP", ""])
    if country == "FR":
        return rng.choice(["IDF", "ARA", "NAQ", "OCC", ""])
    if country == "GB":
        return rng.choice(["ENG", "SCT", "WLS", "NIR", ""])
    return ""


def _profit_ctr_id(idx: int) -> str:
    base = 2_108_991 + (idx * 23) % 7_981_019
    return str(base).zfill(10)[:10]


def build_row(
    company: dict[str, str],
    controlling_area: str,
    client: str,
    idx: int,
    rng: random.Random,
) -> dict[str, str]:
    bukrs = company["CompanyCode"]
    country = _COMPANY_COUNTRY.get(bukrs, "US")
    lang2 = _COMPANY_LANG2.get(bukrs, "EN")
    locales = {"BR": "pt_BR", "US": "en_US", "DE": "de_DE", "FR": "fr_FR", "GB": "en_GB"}
    fk = Faker(locales.get(country, "en_US"))
    fk.seed_instance(int(rng.getrandbits(32)) ^ SYNTHETIC_MASTER_SEED ^ (idx * 31))

    prctr = _profit_ctr_id(idx)
    plant_key = list(MASTER_PLANT_NAMES.keys())[idx % len(MASTER_PLANT_NAMES)]
    plant_label = _normalize_text(MASTER_PLANT_NAMES.get(plant_key, plant_key))[:25]

    area_name = _PC_AREA_NAMES[idx % len(_PC_AREA_NAMES)]
    area_short = _PC_AREA_NAMES_SHORT[idx % len(_PC_AREA_NAMES_SHORT)]
    name_short = _pad(_normalize_text(f"{area_short} {plant_key}"), 20)
    name_long = _pad(_normalize_text(f"{area_name} - {plant_label}")[:40], 40)

    created = _sample_date_between(rng, datetime(2015, 1, 1), datetime(2026, 4, 1))
    valid_from = _sample_date_between(rng, datetime(2016, 1, 1), datetime(2021, 8, 1))
    region = _region_for_country(country, rng)

    user_pc = rng.choice(["PC9980100010", "PC9980100020", "PC9980100030"])
    resp_user = _pad(f"P{user_pc[-8:]}", 12)
    person = _pad(fk.last_name().upper()[:1] + fk.first_name()[:18], 20)

    hier = _pad(f"YDPH-{controlling_area}", 12)
    dept = _pad(_normalize_text(area_name.replace(" ", ""))[:12], 12)

    xf = rng.choice(["", "", "X"])

    fax = ""
    phone1 = ""
    phone2 = ""
    street = ""
    if rng.random() < 0.42:
        phone1 = _pad(re.sub(r"\D", "", fk.phone_number())[:16], 16)
    if rng.random() < 0.12:
        phone2 = _pad(re.sub(r"\D", "", fk.phone_number())[:16], 16)
    if rng.random() < 0.18:
        fax = _pad(re.sub(r"\D", "", fk.phone_number())[:31], 31)
    if rng.random() < 0.38:
        street = _pad(fk.street_address()[:35], 35)

    postal = ""
    district = ""
    if rng.random() < 0.55:
        postal = _pad(fk.postcode()[:10], 10)
    if rng.random() < 0.35:
        district = _pad(fk.city()[:35], 35)

    tax_juris = ""
    if country == "BR" and rng.random() < 0.45:
        tax_juris = _pad(f"BR{rng.choice(['RJ','SP','SC'])}{rng.randint(1, 9):06d}", 15)
    elif rng.random() < 0.15:
        tax_juris = _pad(f"TAX{rng.randint(100000,999999)}", 15)

    pobox = _pad(str(rng.randint(100, 9999)) if rng.random() < 0.06 else "", 10)
    printer = rng.choice(["CO01", "LP01", "LP02", ""]) if rng.random() < 0.25 else ""

    formula = _pad(rng.choice(["", "", "YMPLNV01", "PLANCO2024"])[:10], 10)

    addr3 = ""
    addr4 = ""
    if rng.random() < 0.2:
        addr3 = _pad(fk.company()[:35], 35)
        addr4 = _pad(rng.choice(["Floor", "Block", "Wing"]) + f" {rng.randint(1, 99)}", 35)

    dc_phone = ""
    if rng.random() < 0.12:
        dc_phone = _pad(re.sub(r"\D", "", fk.phone_number())[:14], 14)

    telebox = _pad(str(rng.randint(100000, 9999999)) if rng.random() < 0.04 else "", 15)
    telex = _pad(str(rng.randint(100000, 999999)) if rng.random() < 0.02 else "", 30)

    form_address = rng.choice(["", "", "Firma", "0001"])

    addr_name = _pad(f"Unidade {plant_label}"[:35], 35) if rng.random() > 0.22 else ""

    seg = rng.choice(_SEGMENTS)
    additional = _pad(plant_label[:35], 35) if rng.random() < 0.45 else ""

    return {
        "Client": _pad(client, 3),
        "ControllingArea": _pad(controlling_area, 4),
        "ProfitCenter": _pad(prctr, 10),
        "ValidityEndDate": "99991231",
        "ValidityStartDate": valid_from,
        "CompanyCode": _pad(bukrs, 4),
        "ProfitCenterName": _pad(name_short, 20),
        "ProfitCenterLongName": _pad(name_long, 40),
        "Language": _pad(lang2, 2),
        "AdditionalName": additional,
        "AddressName": addr_name,
        "CityName": _pad(fk.city()[:35], 35),
        "Country": _pad(country, 3),
        "DataCommunicationPhoneNumber": dc_phone,
        "Department": dept,
        "District": district,
        "FaxNumber": fax,
        "FormOfAddress": _pad(form_address, 15),
        "FormulaPlanningTemplate": formula,
        "PhoneNumber1": phone1,
        "PhoneNumber2": phone2,
        "POBox": pobox,
        "PostalCode": postal,
        "ProfitCenterAddrName3": addr3,
        "ProfitCenterAddrName4": addr4,
        "ProfitCenterCreatedByUser": _pad(user_pc, 12),
        "ProfitCenterCreationDate": created,
        "ProfitCenterIsBlocked": xf if rng.random() < 0.05 else "",
        "ProfitCenterPrinterName": _pad(printer, 4),
        "ProfitCenterStandardHierarchy": hier,
        "ProfitCtrResponsiblePersonName": person,
        "ProfitCtrResponsibleUser": resp_user,
        "Region": _pad(region, 3),
        "Segment": _pad(seg, 10),
        "StreetAddressName": street,
        "TaxJurisdiction": tax_juris,
        "TeleboxNumber": telebox,
        "TelexNumber": telex,
    }


def main() -> None:
    repo = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Gera CSV sintetico tipo I_ProfitCenter.")
    parser.add_argument("--output", type=Path, default=repo / "data" / "I_ProfitCenter.csv")
    parser.add_argument(
        "--rows",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Linhas sem header (opcional). Fora de --quick: ajustado ao intervalo "
            f"[{I_PROFITCENTER_MIN_ROWS}, {I_PROFITCENTER_MAX_ROWS}]; "
            f"sem este argumento usa {I_PROFITCENTER_DEFAULT_ROWS}."
        ),
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help=f"Teste rapido: gera exatamente {I_PROFITCENTER_QUICK_TEST_ROWS} linhas.",
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
        args.rows = I_PROFITCENTER_QUICK_TEST_ROWS
    else:
        requested = args.rows if args.rows is not None else I_PROFITCENTER_DEFAULT_ROWS
        if requested < I_PROFITCENTER_MIN_ROWS:
            print(
                f"Aviso: --rows={requested} abaixo do minimo; ajustado a {I_PROFITCENTER_MIN_ROWS}.",
                file=sys.stderr,
            )
        if requested > I_PROFITCENTER_MAX_ROWS:
            print(
                f"Aviso: --rows={requested} acima do maximo; ajustado a {I_PROFITCENTER_MAX_ROWS}.",
                file=sys.stderr,
            )
        args.rows = max(I_PROFITCENTER_MIN_ROWS, min(requested, I_PROFITCENTER_MAX_ROWS))

    rng = random.Random(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for i in range(args.rows):
        co = MASTER_COMPANY_CODES[i % len(MASTER_COMPANY_CODES)]
        kokrs = MASTER_CONTROLLING_AREAS[i % len(MASTER_CONTROLLING_AREAS)]
        client = args.client.strip()[:3] if args.client else MASTER_CLIENT_IDS[i % len(MASTER_CLIENT_IDS)]
        rows.append(build_row(co, kokrs, client, i, rng))

    out_cols = [c for c in _PROFITCENTER_COLUMNS if any(csv_cell_has_semantic_value(r.get(c)) for r in rows)]
    with args.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in out_cols})

    print(f"Escrito {args.rows} linhas ({len(out_cols)} colunas) em {args.output.resolve()}")


if __name__ == "__main__":
    main()
