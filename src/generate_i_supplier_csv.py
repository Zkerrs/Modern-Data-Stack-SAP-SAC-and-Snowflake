"""
CSV sintético `I_SUPPLIER_CDS` (I_Supplier). Geração cobre todos os elementos CDS;
no ficheiro gravam-se **somente** colunas com pelo menos um valor numa linha —
colunas sempre vazias em todas as linhas são omitidas.

Valores alinhados ao I_Customer: para cada LIFNR, usa-se a primeira linha de cliente
com Supplier = LIFNR para campos semanticamente comuns.

Uso:
  python src/generate_i_supplier_csv.py --from-customer-csv data/I_Customer.csv --output data/I_Supplier.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import random
import string
from datetime import datetime, timedelta
from pathlib import Path

from sap_synthetic_masters import (
    DEFAULT_START_SUPPLIER_NUMBER,
    MASTER_CLIENT_IDS,
    MASTER_PLANTS,
    MASTER_SUPPLIER_ACCOUNT_GROUPS,
    SYNTHETIC_MASTER_SEED,
    column_order_excluding_always_empty,
    pad_kunnr_lifnr,
)

# Ordem conforme elementos I_SUPPLIER_CDS (S/4HANA); nomes OData PascalCase.
SUPPLIER_COLUMNS = [
    "Client",
    "Supplier",
    "SupplierAccountGroup",
    "SupplierName",
    "SupplierFullName",
    "IsBusinessPurposeCompleted",
    "CreatedByUser",
    "CreationDate",
    "IsOneTimeAccount",
    "AuthorizationGroup",
    "VatRegistration",
    "AccountIsBlockedForPosting",
    "TaxJurisdiction",
    "SupplierCorporateGroup",
    "Customer",
    "Industry",
    "TaxNumber1",
    "TaxNumber2",
    "TaxNumber3",
    "TaxNumber4",
    "TaxNumber5",
    "TaxNumber6",
    "PostingIsBlocked",
    "PurchasingIsBlocked",
    "InternationalAllocationNumber1",
    "InternationalAllocationNumber2",
    "InternationalAllocationNumber3",
    "AddressId",
    "Region",
    "OrganizationBpName1",
    "OrganizationBpName2",
    "CityName",
    "PostalCode",
    "StreetName",
    "Country",
    "ConcatenatedInternationAllocNo",
    "SupplierProcurementBlock",
    "SuplrQualityManagementSystem",
    "SuplrQltyInProcmtCertfnValidTo",
    "SupplierLanguage",
    "AlternativePayeeAccountNumber",
    "PhoneNumber1",
    "FaxNumber",
    "IsNaturalPerson",
    "TaxNumberResponsible",
    "UkContractorBusinessType",
    "UkPartnerTradingName",
    "UkPartnerTaxReference",
    "UkVerificationStatus",
    "UkVerificationNumber",
    "UkCompanyRegistrationNumber",
    "UkVerifiedTaxStatus",
    "FormOfAddress",
    "ReferenceAccountGroup",
    "VatLiability",
    "ResponsibleType",
    "TaxNumberType",
    "FiscalAddress",
    "BusinessType",
    "BirthDate",
    "PaymentIsBlockedForSupplier",
    "SortField",
    "PhoneNumber2",
    "DeletionIndicator",
    "TaxInvoiceRepresentativeName",
    "IndustryType",
    "InGstSupplierClassification",
    "SuplrProofOfDelivRlvtCode",
    "TradingPartner",
    "BrTaxIsSplit",
    "AuPayerIsPayingToCarryOnEnt",
    "AuIndividualIsUnder18",
    "AuPaymentIsExceeding75",
    "AuPaymentIsWhollyInputTaxed",
    "AuPartnerIsSupplyWithoutGain",
    "AuSupplierIsEntitledToAbn",
    "AuPaymentIsIncomeExempted",
    "AuSupplyIsMadeAsPrivateHobby",
    "AuSupplyMadeIsOfDmstcNature",
    "IsToBeAcceptedAtOrigin",
    "BpiIsEqualizationTaxSubject",
    "BrSpcfCtTaxBasePercentageCode",
    "DataMediumExchangeIndicator",
    "DataExchangeInstructionKey",
    "SupplierIsSubrangeRelevant",
    "TrainStationName",
    "AlternativePayeeIsAllowed",
    "PaytslipWithRefSubscriber",
    "TranspServiceAgentStstcGrp",
    "SupplierIsPlantRelevant",
    "SuplrTaxAuthorityAccountNumber",
    "SupplierPlant",
    "FactoryCalendar",
    "PaymentReason",
]


def _err(msg: str) -> None:
    raise SystemExit(msg)


def _one_line(s: str) -> str:
    return " ".join((s or "").replace("\r", " ").replace("\n", " ").split()).strip()


def _digits(rng: random.Random, n: int) -> str:
    return "".join(rng.choice(string.digits) for _ in range(n))


def _clip(s: str, n: int) -> str:
    return (s or "")[:n]


def collect_first_anchor_by_supplier(csv_path: Path) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    with csv_path.open(newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        if not rdr.fieldnames:
            _err("CSV de cliente sem header.")
        for row in rdr:
            sup = _one_line(row.get("Supplier", ""))
            if not sup:
                continue
            if sup not in out:
                out[sup] = {k: (v if v is not None else "") for k, v in row.items()}
    return out


def _sample_customers(csv_path: Path, limit: int = 5000) -> list[str]:
    seen: list[str] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            k = _one_line(row.get("Customer", ""))
            if k and k not in seen:
                seen.append(k)
            if len(seen) >= limit:
                break
    return seen


def _fictitious_supplier_names(supplier_id: str, country: str) -> tuple[str, str, str]:
    from faker import Faker

    h = int(hashlib.sha256(supplier_id.encode("utf-8")).hexdigest()[:12], 16)
    rng = random.Random(h ^ SYNTHETIC_MASTER_SEED)
    locales_map = {
        "DE": "de_DE",
        "BR": "pt_BR",
        "US": "en_US",
        "GB": "en_GB",
        "UK": "en_GB",
        "FR": "fr_FR",
        "MX": "es_MX",
        "CA": "en_CA",
        "IT": "it_IT",
        "ES": "es_ES",
        "JP": "ja_JP",
        "PT": "pt_PT",
    }
    lc = locales_map.get(country, "en_US")
    fk = Faker(lc)
    fk.seed_instance(int(rng.getrandbits(32)))
    n1 = _one_line(fk.company())[:35]
    n2 = rng.choice(["Materiais", "Componentes", "Logistica", "Servicos Industriais"])[:35]
    full = _one_line(f"{n1} - {n2}")[:220]
    short = full[:80]
    sortf = "".join(c for c in n1.upper() if c.isalnum())[:10] or supplier_id.strip()[-6:]
    return short, full, sortf


def build_row_from_anchor(
    supplier_id: str,
    cr: dict[str, str],
    global_rng: random.Random,
) -> dict[str, str]:
    country = _clip(cr.get("Country", ""), 3)
    client = _clip(cr.get("Client", "") or "", 3) or global_rng.choice(MASTER_CLIENT_IDS)
    customer_kunnr = _clip(cr.get("Customer", "") or "", 10)

    sname, sfull, sortf = _fictitious_supplier_names(supplier_id, country)
    grp = global_rng.choice(MASTER_SUPPLIER_ACCOUNT_GROUPS)

    iln1 = _clip(cr.get("InternationalAllocationNumber1", ""), 7)
    iln2 = _clip(cr.get("InternationalAllocationNumber2", ""), 5)
    iln3 = _clip(cr.get("InternationalAllocationNumber3", ""), 1)
    concat = _clip(iln1 + iln2 + iln3, 20)

    corp = _clip(cr.get("CustomerCorporateGroup", ""), 10)

    bd = ""
    if global_rng.random() < 0.01:
        d0 = datetime(1960, 1, 1) + timedelta(days=global_rng.randint(0, 20000))
        bd = d0.strftime("%Y%m%d")

    plant = global_rng.choice(MASTER_PLANTS)
    tt = _clip(cr.get("TaxNumberType", ""), 2)

    return {
        "Client": client,
        "Supplier": _clip(supplier_id, 10),
        "SupplierAccountGroup": grp,
        "SupplierName": sname,
        "SupplierFullName": sfull,
        "IsBusinessPurposeCompleted": _clip(cr.get("IsBusinessPurposeCompleted", ""), 1),
        "CreatedByUser": _clip(cr.get("CreatedByUser", ""), 12),
        "CreationDate": _clip(cr.get("CreationDate", ""), 8),
        "IsOneTimeAccount": _clip(cr.get("IsOneTimeAccount", ""), 1),
        "AuthorizationGroup": _clip(cr.get("AuthorizationGroup", ""), 4),
        "VatRegistration": _clip(cr.get("VatRegistration", ""), 20),
        "AccountIsBlockedForPosting": _clip(cr.get("PostingIsBlocked", ""), 1),
        "TaxJurisdiction": _clip(cr.get("TaxJurisdiction", ""), 15),
        "SupplierCorporateGroup": corp,
        "Customer": customer_kunnr,
        "Industry": _clip(cr.get("Industry", ""), 4),
        "TaxNumber1": _clip(cr.get("TaxNumber1", ""), 16),
        "TaxNumber2": _clip(cr.get("TaxNumber2", ""), 11),
        "TaxNumber3": _clip(cr.get("TaxNumber3", ""), 18),
        "TaxNumber4": _clip(cr.get("TaxNumber4", ""), 18),
        "TaxNumber5": _clip(cr.get("TaxNumber5", ""), 60),
        "TaxNumber6": _clip(cr.get("TaxNumber6", ""), 20),
        "PostingIsBlocked": _clip(cr.get("PostingIsBlocked", ""), 1),
        "PurchasingIsBlocked": "X" if global_rng.random() < 0.02 else "",
        "InternationalAllocationNumber1": iln1,
        "InternationalAllocationNumber2": iln2,
        "InternationalAllocationNumber3": iln3,
        "AddressId": _clip(cr.get("AddressId", ""), 10),
        "Region": _clip(cr.get("Region", ""), 3),
        "OrganizationBpName1": _clip(_one_line(sname), 35),
        "OrganizationBpName2": _clip(
            _one_line(cr.get("OrganizationBpName2", "") or "")
            or global_rng.choice(
                [
                    "Suprimentos Industriais",
                    "Logistica e Distribuicao",
                    "Componentes Tecnicos",
                    "Operacoes Comerciais",
                ]
            ),
            35,
        ),
        "CityName": _clip(cr.get("CityName", ""), 35),
        "PostalCode": _clip(cr.get("PostalCode", ""), 10),
        "StreetName": _clip(cr.get("StreetName", ""), 35),
        "Country": country,
        "ConcatenatedInternationAllocNo": concat,
        "SupplierProcurementBlock": "" if global_rng.random() > 0.97 else global_rng.choice(["01", "02"])[:2],
        "SuplrQualityManagementSystem": "" if global_rng.random() > 0.94 else _digits(global_rng, 4),
        "SuplrQltyInProcmtCertfnValidTo": "",
        "SupplierLanguage": _clip(cr.get("Language", "") or "", 1),
        "AlternativePayeeAccountNumber": "",
        "PhoneNumber1": _clip(cr.get("TelephoneNumber1", ""), 16),
        "FaxNumber": _clip(cr.get("FaxNumber", ""), 31),
        "IsNaturalPerson": _clip(cr.get("NfPartnerIsNaturalPerson", ""), 1),
        "TaxNumberResponsible": "",
        "UkContractorBusinessType": "",
        "UkPartnerTradingName": "",
        "UkPartnerTaxReference": "",
        "UkVerificationStatus": "",
        "UkVerificationNumber": "",
        "UkCompanyRegistrationNumber": "",
        "UkVerifiedTaxStatus": "",
        "FormOfAddress": "",
        "ReferenceAccountGroup": "",
        "VatLiability": _clip(cr.get("VatLiability", ""), 1),
        "ResponsibleType": _clip(cr.get("ResponsibleType", ""), 2),
        "TaxNumberType": tt,
        # FISCALADDRESS no credor refere LIFNR de escritorio fiscal — nao reutiliza KUNNR do cliente.
        "FiscalAddress": "",
        "BusinessType": _clip(_one_line(cr.get("BusinessType", "")), 30),
        "BirthDate": bd,
        "PaymentIsBlockedForSupplier": "",
        "SortField": sortf,
        "PhoneNumber2": _clip(cr.get("TelephoneNumber2", ""), 16),
        "DeletionIndicator": _clip(cr.get("DeletionIndicator", ""), 1),
        "TaxInvoiceRepresentativeName": _clip(cr.get("TaxInvoiceRepresentativeName", ""), 10),
        "IndustryType": _clip(_one_line(cr.get("IndustryType", "")), 30),
        "InGstSupplierClassification": "",
        "SuplrProofOfDelivRlvtCode": "",
        "TradingPartner": _clip(cr.get("TradingPartner", ""), 6),
        "BrTaxIsSplit": "",
        "AuPayerIsPayingToCarryOnEnt": "",
        "AuIndividualIsUnder18": "",
        "AuPaymentIsExceeding75": "",
        "AuPaymentIsWhollyInputTaxed": "",
        "AuPartnerIsSupplyWithoutGain": "",
        "AuSupplierIsEntitledToAbn": "",
        "AuPaymentIsIncomeExempted": "",
        "AuSupplyIsMadeAsPrivateHobby": "",
        "AuSupplyMadeIsOfDmstcNature": "",
        "IsToBeAcceptedAtOrigin": "",
        "BpiIsEqualizationTaxSubject": "",
        "BrSpcfCtTaxBasePercentageCode": "",
        "DataMediumExchangeIndicator": _clip(cr.get("DataMediumExchangeIndicator", ""), 1),
        "DataExchangeInstructionKey": "",
        "SupplierIsSubrangeRelevant": "",
        "TrainStationName": _clip(_one_line(cr.get("TrainStationName", "")), 25),
        "AlternativePayeeIsAllowed": _clip(cr.get("AlternativePayeeIsAllowed", ""), 1),
        "PaytslipWithRefSubscriber": "",
        "TranspServiceAgentStstcGrp": "",
        "SupplierIsPlantRelevant": "X" if global_rng.random() < 0.08 else "",
        "SuplrTaxAuthorityAccountNumber": "",
        "SupplierPlant": plant,
        "FactoryCalendar": "" if global_rng.random() > 0.94 else global_rng.choice(["01", "02"])[:2],
        "PaymentReason": "",
    }


def build_synthetic_standalone_supplier(
    numeric_id: int,
    global_rng: random.Random,
    customer_pool: list[str],
    existing_suppliers: set[str],
) -> dict[str, str] | None:
    lid = pad_kunnr_lifnr(numeric_id)
    if lid in existing_suppliers:
        return None
    country = global_rng.choice(["BR", "US", "DE", "FR", "GB"])
    client = global_rng.choice(MASTER_CLIENT_IDS)

    fk_cust = global_rng.choice(customer_pool) if customer_pool else ""

    _city_by_country = {
        "BR": "Campinas",
        "US": "Chicago",
        "DE": "Hamburg",
        "FR": "Lyon",
        "GB": "Manchester",
    }
    _street_by_country = {
        "BR": "Avenida Industrial 1500",
        "US": "Industrial Park Ave 250",
        "DE": "Industriestrasse 44",
        "FR": "Rue de l Industrie 18",
        "GB": "Commerce Road 32",
    }

    row_like: dict[str, str] = {
        "Country": country,
        "Customer": fk_cust,
        "PostalCode": _digits(global_rng, 8) if country == "BR" else _digits(global_rng, 5),
        "CityName": _city_by_country.get(country, "Chicago"),
        "StreetName": _street_by_country.get(country, "Industrial Park Ave 100"),
        "Region": "",
        "AddressId": _digits(global_rng, 10),
        "TaxJurisdiction": (country + _digits(global_rng, 10))[:15],
        "Industry": str(global_rng.randint(1000, 9999)),
        "TaxNumberType": global_rng.choice(["", "BR1", "DE0"]),
        "TaxNumber1": (_digits(global_rng, 14))[:16],
        "IndustryType": "",
        "BusinessType": "",
        "VatRegistration": "",
        "IsBusinessPurposeCompleted": "",
        "CreatedByUser": "".join(global_rng.choice(string.ascii_uppercase) for _ in range(8)),
        "CreationDate": "20200101",
        "Language": {"BR": "P", "US": "E", "DE": "D", "FR": "F", "GB": "E"}.get(country, "E"),
        "PostingIsBlocked": "",
        "IsOneTimeAccount": "",
        "AuthorizationGroup": "",
        "DeletionIndicator": "",
        "TradingPartner": "",
        "InternationalAllocationNumber1": str(global_rng.randint(0, 9_999_999)).zfill(7),
        "InternationalAllocationNumber2": str(global_rng.randint(0, 99_999)).zfill(5),
        "InternationalAllocationNumber3": str(global_rng.randint(0, 9)),
        "TelephoneNumber1": "",
        "TelephoneNumber2": "",
        "FaxNumber": "",
        "NfPartnerIsNaturalPerson": "",
        "ResponsibleType": "",
        "DataMediumExchangeIndicator": "",
        "TaxInvoiceRepresentativeName": "",
        "VatLiability": "",
        "FiscalAddress": "",
        "TrainStationName": "",
        "AlternativePayeeIsAllowed": "",
        "CustomerCorporateGroup": "",
    }

    r = build_row_from_anchor(lid, row_like | {"Client": client}, global_rng)
    r["Client"] = client
    return r


def main() -> None:
    repo = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Gera I_Supplier.csv alinhado a I_Customer.csv.")
    parser.add_argument("--from-customer-csv", type=Path, default=repo / "data" / "I_Customer.csv")
    parser.add_argument("--output", type=Path, default=repo / "data" / "I_Supplier.csv")
    parser.add_argument("--seed", type=int, default=SYNTHETIC_MASTER_SEED)
    parser.add_argument("--extras", type=int, default=0)
    args = parser.parse_args()

    if not args.from_customer_csv.is_file():
        _err(f"Arquivo nao encontrado: {args.from_customer_csv}")

    anchors = collect_first_anchor_by_supplier(args.from_customer_csv)
    rng = random.Random(args.seed)
    customers = _sample_customers(args.from_customer_csv)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    existing: set[str] = set(anchors.keys())

    rows_out: list[dict[str, str]] = []
    for sid in sorted(anchors.keys()):
        row = build_row_from_anchor(sid, anchors[sid], rng)
        rows_out.append(row)
        written += 1

    idx = DEFAULT_START_SUPPLIER_NUMBER
    added = 0
    guard = 0
    while added < args.extras and guard < args.extras * 20:
        guard += 1
        idx += 1
        row = build_synthetic_standalone_supplier(idx, rng, customers, existing)
        if row is None:
            continue
        sid = row["Supplier"]
        if sid in existing:
            continue
        existing.add(sid)
        rows_out.append(row)
        written += 1
        added += 1

    out_cols = column_order_excluding_always_empty(SUPPLIER_COLUMNS, rows_out)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_cols)
        w.writeheader()
        for row in rows_out:
            w.writerow({k: row[k] for k in out_cols})

    print(f"Escrito {written} linhas ({len(out_cols)} colunas) em {args.output.resolve()}")


if __name__ == "__main__":
    main()
