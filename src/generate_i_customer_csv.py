"""
CSV sintético espelho da view CDS S/4HANA `I_CUSTOMER_CDS` (I_Customer, PascalCase).

- Em código mantém-se a lista completa de elementos CDS para gerar linhas coerentes.
- No ficheiro CSV **omitem-se apenas** colunas em que **todas** as linhas ficarem vazias
  (mantém-se a coluna se existir pelo menos uma célula com valor).
- Execução normal: **entre 120 000 e 150 000 linhas** (valores fora são ajustados com aviso).
- Testes: **`--quick`** gera **600** linhas.

Uso:
  python src/generate_i_customer_csv.py [--rows N] --output data/I_Customer.csv

Requer: pip install faker tqdm
"""

from __future__ import annotations

import argparse
import csv
import random
import string
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from sap_synthetic_masters import (
    DEFAULT_START_CUSTOMER_NUMBER,
    I_CUSTOMER_DEFAULT_ROWS,
    I_CUSTOMER_MAX_ROWS,
    I_CUSTOMER_MIN_ROWS,
    I_CUSTOMER_QUICK_TEST_ROWS,
    MASTER_CLIENT_IDS,
    MASTER_CUSTOMER_ACCOUNT_GROUPS,
    SYNTHETIC_MASTER_SEED,
    csv_cell_has_semantic_value,
)

# Ordem conforme elementos da estrutura de persistencia CDS I_CUSTOMER_CDS no S/4HANA (release tipico ABAP CDS).
COLUMNS = [
    "Client",
    "Customer",
    "CustomerName",
    "CustomerFullName",
    "CreatedByUser",
    "CreationDate",
    "AddressId",
    "CustomerClassification",
    "VatRegistration",
    "CustomerAccountGroup",
    "AuthorizationGroup",
    "DeliveryIsBlocked",
    "PostingIsBlocked",
    "BillingIsBlockedForCustomer",
    "OrderIsBlockedForCustomer",
    "InternationalAllocationNumber1",
    "IsOneTimeAccount",
    "TaxJurisdiction",
    "Industry",
    "TaxNumberType",
    "TaxNumber1",
    "TaxNumber2",
    "TaxNumber3",
    "TaxNumber4",
    "TaxNumber5",
    "TaxNumber6",
    "CustomerCorporateGroup",
    "Supplier",
    "NielsenRegion",
    "IndustryCode1",
    "IndustryCode2",
    "IndustryCode3",
    "IndustryCode4",
    "IndustryCode5",
    "Country",
    "OrganizationBpName1",
    "OrganizationBpName2",
    "CityName",
    "PostalCode",
    "StreetName",
    "SortField",
    "FaxNumber",
    "BrSuframaCode",
    "Region",
    "TelephoneNumber1",
    "TelephoneNumber2",
    "AlternativePayerAccount",
    "DataMediumExchangeIndicator",
    "VatLiability",
    "IsBusinessPurposeCompleted",
    "ResponsibleType",
    "FiscalAddress",
    "NfPartnerIsNaturalPerson",
    "DeletionIndicator",
    "Language",
    "TradingPartner",
    "DeliveryDateTypeRule",
    "ExpressTrainStationName",
    "TrainStationName",
    "InternationalAllocationNumber2",
    "InternationalAllocationNumber3",
    "CityCode",
    "County",
    "CustomerHasUnloadingPoint",
    "CustomerWorkingTimeCalendar",
    "IsCompetitor",
    "TaxInvoiceRepresentativeName",
    "BusinessType",
    "IndustryType",
    "TwCollvBillingIsSupported",
    "AlternativePayeeIsAllowed",
    "FreeDefinedAttribute01",
    "FreeDefinedAttribute02",
    "FreeDefinedAttribute03",
    "FreeDefinedAttribute04",
    "FreeDefinedAttribute05",
    "FreeDefinedAttribute06",
    "FreeDefinedAttribute07",
    "FreeDefinedAttribute08",
    "FreeDefinedAttribute09",
    "FreeDefinedAttribute10",
]

REGIONS_BY_COUNTRY: dict[str, list[str]] = {
    "DE": ["BY", "BE", "NW", "BW", "HE"],
    "BR": ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "GO"],
    "US": ["NY", "CA", "TX", "IL", "FL", "WA", "MA", "CO"],
    "GB": ["LDN", "MAN", "BIR", "GLS", "YKS"],
    "FR": ["IDF", "ARA", "NAQ", "OCC", "HDF"],
    "MX": ["CMX", "JAL", "NL", "QUE", "YUC"],
    "CA": ["ON", "BC", "AB", "QC"],
    "IT": ["LMI", "LAZ", "VEN", "SIC"],
    "ES": ["MAD", "CAT", "AND", "VAS"],
}

LANG_BY_COUNTRY: dict[str, str] = {
    "DE": "D",
    "BR": "P",
    "US": "E",
    "GB": "E",
    "FR": "F",
    "MX": "S",
    "CA": "E",
    "IT": "I",
    "ES": "S",
    "JP": "J",
    "PT": "P",
}


def _digits(rng: random.Random, n: int) -> str:
    return "".join(rng.choice(string.digits) for _ in range(n))


def _alnum(rng: random.Random, n: int) -> str:
    pool = string.ascii_uppercase + string.digits
    return "".join(rng.choice(pool) for _ in range(n))


def _maybe(rng: random.Random, prob: float) -> bool:
    return rng.random() < prob


def _pad_num(s: str, length: int) -> str:
    return s.zfill(length)[:length]


def _one_line(s: str) -> str:
    """Evita newline dentro de campo CSV (Faker pode injetar quebra em address)."""
    return " ".join(s.replace("\r", " ").replace("\n", " ").split()).strip()


def _random_date(rng: random.Random) -> str:
    start = datetime(2012, 1, 1)
    end = datetime(2026, 5, 1)
    delta = end - start
    d = start + timedelta(days=rng.randint(0, max(0, delta.days)))
    return d.strftime("%Y%m%d")


def _postal(country: str, rng: random.Random) -> str:
    if country == "DE":
        return _pad_num(str(rng.randint(10000, 99999)), 5)
    if country == "BR":
        return _pad_num(str(rng.randint(1000000, 99999999)), 8)
    if country == "US":
        return _pad_num(str(rng.randint(10000, 99999)), 5)
    if country == "GB":
        outward = "".join(rng.choice(string.ascii_uppercase) for _ in range(2)) + _digits(rng, 1)
        inward = _digits(rng, 3) + rng.choice(string.ascii_uppercase) + rng.choice(string.ascii_uppercase)
        return f"{outward}{inward}"[:10]
    if country == "FR":
        return _pad_num(str(rng.randint(10000, 99999)), 5)
    return _pad_num(str(rng.randint(1000, 99999)), rng.choice([5, 6]))


def _suffix_for_country(country: str, rng: random.Random) -> str:
    pool = {
        "DE": ["GmbH", "AG", "KG", "SE"],
        "BR": ["LTDA", "S.A.", "EIRELI", "ME"],
        "US": ["Inc.", "LLC", "Corp.", "Holdings"],
        "GB": ["Ltd", "PLC", "LLP"],
        "FR": ["SAS", "SARL", "SA"],
        "MX": ["S.A. de C.V.", "S. de R.L."],
        "CA": ["Inc.", "Corp.", "Ltd."],
        "IT": ["S.r.l.", "S.p.A."],
        "ES": ["S.L.", "S.A."],
        "JP": ["株式会社", "有限会社"],
        "PT": ["Lda.", "S.A."],
    }.get(country, ["Ltd"])
    return rng.choice(pool)


@dataclass
class FakeContext:
    rng: random.Random
    faker_en: object
    faker_local: dict[str, object]


def _build_fakers(seed: int | None) -> FakeContext:
    from faker import Faker

    rng = random.Random(seed)
    primary = Faker(
        [
            "en_US",
            "pt_BR",
            "de_DE",
            "fr_FR",
            "es_ES",
            "it_IT",
            "ja_JP",
            "en_GB",
        ]
    )
    primary.seed_instance(seed if seed is not None else rng.randint(0, 2**31 - 1))
    locales = {
        "DE": Faker("de_DE"),
        "BR": Faker("pt_BR"),
        "US": Faker("en_US"),
        "GB": Faker("en_GB"),
        "FR": Faker("fr_FR"),
        "MX": Faker("es_MX"),
        "CA": Faker("en_CA"),
        "IT": Faker("it_IT"),
        "ES": Faker("es_ES"),
        "JP": Faker("ja_JP"),
        "PT": Faker("pt_PT"),
    }
    ls = seed if seed is not None else rng.randint(0, 2**31 - 1)
    for f in locales.values():
        f.seed_instance(ls)
    return FakeContext(rng=rng, faker_en=primary, faker_local=locales)


def _company_line(ctx: FakeContext, country: str) -> tuple[str, str, str, str]:
    rng = ctx.rng
    loc = ctx.faker_local.get(country, ctx.faker_en)
    suffix = _suffix_for_country(country, rng)

    templates = []
    primary = loc.company().split(",")[0][:35].strip()
    if rng.random() < 0.65:
        name1 = primary[:35]
        part = rng.choice(
            [
                "Logistics",
                "Trading",
                "Wholesale",
                "Industrial",
                "Foods",
                "Pharma",
                "Tech",
                "Metals",
                "Packaging",
                "Maritime",
                "Automotive",
                "Electronics",
                "Chemicals",
                "Retail",
                "Systems",
            ]
        )
        name2 = f"{part} {suffix}"[:35]
    else:
        name1 = primary[:35]
        name2 = rng.choice(
            [
                "Operations",
                "Procurement",
                "Shared Services",
                "Export",
                "Import",
                "Regional Hub",
                "Distribution",
            ]
        )[:35]

    name1 = _one_line(name1)
    name2 = _one_line(name2)

    short = "".join(c for c in name1.upper() if c.isalnum())[:10] or _alnum(rng, 6)
    full = _one_line(f"{name1} - {name2}".strip(" -"))[:220]
    return name1, name2, full, short


def _phones(country: str, rng: random.Random) -> tuple[str, str, str]:
    if country == "BR":
        ddd = rng.randint(11, 99)
        n1 = f"+55{ddd}9{rng.randint(10000000, 99999999)}"
        n2 = f"+55{ddd}{rng.randint(30000000, 39999999)}" if _maybe(rng, 0.4) else ""
        fax = f"+55{ddd}{rng.randint(20000000, 29999999)}" if _maybe(rng, 0.15) else ""
        return n1, n2, fax
    if country == "DE":
        n1 = f"+49{rng.randint(30, 89)}{rng.randint(1000000, 9999999)}"
        n2 = f"+49{rng.randint(30, 89)}{rng.randint(1000000, 9999999)}" if _maybe(rng, 0.35) else ""
        fax = f"+49{rng.randint(30, 89)}{rng.randint(1000000, 9999999)}" if _maybe(rng, 0.12) else ""
        return n1, n2, fax
    if country in ("US", "CA"):
        ac = rng.randint(200, 999)
        n1 = f"+1{ac}{rng.randint(2000000, 9999999)}"
        n2 = f"+1{rng.randint(200, 999)}{rng.randint(2000000, 9999999)}" if _maybe(rng, 0.4) else ""
        fax = "" if not _maybe(rng, 0.1) else f"+1{ac}{rng.randint(2000000, 9999999)}"
        return n1, n2, fax
    n1 = f"+{rng.randint(20, 90)}{rng.randint(100000000, 999999999)}"
    n2 = f"+{rng.randint(20, 90)}{rng.randint(100000000, 999999999)}" if _maybe(rng, 0.3) else ""
    fax = f"+{rng.randint(20, 90)}{rng.randint(100000000, 999999999)}" if _maybe(rng, 0.1) else ""
    return n1, n2, fax


def _tax_numbers(country: str, rng: random.Random) -> tuple[str, str, str, str, str, str, str]:
    t1 = t2 = t3 = t4 = t5 = t6 = ""
    tt = rng.choice(["", "BR1", "DE0", "US0", "GB0", "FR0", "MX0"])

    def only_digits(s: str, mx: int) -> str:
        s = "".join(ch for ch in s if ch.isdigit())[:mx]
        return s

    if country == "BR":
        base = only_digits("".join(rng.choice(string.digits) for _ in range(14)), 14)
        t1 = base.ljust(16)[:16] or _digits(rng, 14)
    elif country == "DE":
        t1 = f"DE{_digits(rng, 9)}"
    elif country == "US":
        t1 = f"{rng.randint(10, 99)}-{rng.randint(1000000, 9999999)}"
    elif country == "GB":
        t1 = f"GB{rng.randint(100, 999)}{_digits(rng, 9)}"
    else:
        t1 = _alnum(rng, rng.randint(8, 16))

    if _maybe(rng, 0.25):
        t2 = _digits(rng, 11)
    if _maybe(rng, 0.08):
        t3 = _alnum(rng, 18)
    if _maybe(rng, 0.05):
        t4 = _alnum(rng, 18)
    if _maybe(rng, 0.03):
        t5 = _alnum(rng, min(60, rng.randint(10, 60)))
    if _maybe(rng, 0.03):
        t6 = _alnum(rng, 20)

    return tt, t1, t2, t3, t4, t5, t6


def _free_attr(rng: random.Random, width: int) -> str:
    if _maybe(rng, 0.12):
        return ""
    chars = string.ascii_uppercase + string.digits
    return "".join(rng.choice(chars) for _ in range(width))


def generate_row(ctx: FakeContext, customer_numeric: int) -> dict[str, str]:
    rng = ctx.rng
    country_weights = ["DE"] * 10 + ["BR"] * 18 + ["US"] * 16 + ["GB"] * 8 + ["FR"] * 8 + ["MX"] * 7 + ["CA"] * 5 + ["IT"] * 8 + ["ES"] * 7 + ["JP"] * 5 + ["PT"] * 4
    country = rng.choice(country_weights)

    client = rng.choice(MASTER_CLIENT_IDS)

    cust = _pad_num(str(customer_numeric), 10)

    name1, name2, full_name, sort_key = _company_line(ctx, country)
    cre_user = "".join(rng.choice(string.ascii_uppercase + string.digits) for _ in range(rng.randint(5, 12)))
    cre_date = _random_date(rng)
    addr = _pad_num(str(rng.randint(1, 9_999_999)), 10)

    loc_f = ctx.faker_local.get(country, ctx.faker_en)
    city = _one_line(loc_f.city())[:35]
    street = _one_line(loc_f.street_address())[:35]

    kla = rng.choice(["01", "02", "03", "", ""]) if _maybe(rng, 0.7) else ""
    account_group = rng.choice(MASTER_CUSTOMER_ACCOUNT_GROUPS)
    auth = _alnum(rng, 4) if _maybe(rng, 0.08) else ""

    del_block = rng.choice(["", "SP", "90"]) if _maybe(rng, 0.04) else ""
    post_block = rng.choice(["", "", "", "X"]) if _maybe(rng, 0.02) else ""
    bill_block = rng.choice(["", "01"]) if _maybe(rng, 0.03) else ""
    ord_block = rng.choice(["", "02"]) if _maybe(rng, 0.03) else ""

    iln1 = _pad_num(str(rng.randint(0, 9_999_999)), 7)
    one_time = "X" if _maybe(rng, 0.02) else ""

    txjcd = ""
    if _maybe(rng, 0.6):
        txjcd = (country + _digits(rng, 10))[:15]

    industry = _pad_num(str(rng.randint(0, 9999)), 4)
    tt, t1, t2, t3, t4, t5, t6 = _tax_numbers(country, rng)

    corp = _pad_num(str(rng.randint(0, 999999)), 10) if _maybe(rng, 0.12) else ""
    supplier = _pad_num(str(rng.randint(0, 999999)), 10) if _maybe(rng, 0.15) else ""

    nielsen = rng.choice(["", "", "AA", "AB", "C1"])

    ic = [_alnum(rng, rng.randint(0, 10)) if _maybe(rng, 0.4) else "" for _ in range(5)]

    phone1, phone2, fax = _phones(country, rng)
    postal = _postal(country, rng)
    region = rng.choice(REGIONS_BY_COUNTRY.get(country, ["XX"])) if _maybe(rng, 0.85) else ""

    alt_payer = cust if _maybe(rng, 0.06) else ""
    dmei = rng.choice(["", "1"]) if _maybe(rng, 0.35) else ""
    vliab = rng.choice(["", "", "X"]) if _maybe(rng, 0.2) else ""
    bus_done = rng.choice(["", "X"]) if _maybe(rng, 0.05) else ""
    resp_tp = rng.choice(["", "", "01", "02"]) if country == "BR" and _maybe(rng, 0.08) else ""
    fiscal_addr = _pad_num(str(rng.randint(0, 9_999_999)), 10) if _maybe(rng, 0.04) else ""

    nf_nat = rng.choice(["", "X"]) if _maybe(rng, 0.03) else ""
    del_ind = rng.choice(["", "", "", "", "X"]) if _maybe(rng, 0.01) else ""

    lang = LANG_BY_COUNTRY.get(country, "E")
    tp = _pad_num(str(rng.randint(0, 880000)), 6) if _maybe(rng, 0.12) else ""
    deliv_rule = rng.choice(["", "A", "B"]) if _maybe(rng, 0.06) else ""
    bahn_exp = _one_line(" ".join(loc_f.words(nb=2)))[:25] if _maybe(rng, 0.02) else ""
    bahn = _one_line(" ".join(loc_f.words(nb=2)))[:25] if _maybe(rng, 0.02) else ""
    iln2 = _pad_num(str(rng.randint(0, 99_999)), 5)
    iln3 = str(rng.randint(0, 9))

    city_code = _alnum(rng, 4) if _maybe(rng, 0.55) else ""
    county = _alnum(rng, 3) if _maybe(rng, 0.45) else ""
    unloading = rng.choice(["", "X"]) if _maybe(rng, 0.15) else ""
    work_cal = rng.choice(["", "01", "02"]) if _maybe(rng, 0.08) else ""
    competitor = rng.choice(["", "X"]) if _maybe(rng, 0.02) else ""
    repr_name = _alnum(rng, 10) if _maybe(rng, 0.06) else ""
    biz_type = _one_line(" ".join(loc_f.words(nb=3)))[:30] if _maybe(rng, 0.25) else ""
    ind_type = _one_line(" ".join(loc_f.words(nb=3)))[:30] if _maybe(rng, 0.25) else ""

    tw = rng.choice(["", "X"]) if _maybe(rng, 0.01) else ""
    alt_pay_allow = rng.choice(["", "", "X"]) if _maybe(rng, 0.1) else ""

    free = [_free_attr(rng, w) for w in [2, 2, 2, 2, 2, 3, 3, 3, 3, 3]]

    vatreg = ""
    if country == "DE" and _maybe(rng, 0.7):
        vatreg = f"DE{_digits(rng, 9)}"
    elif country == "BR" and _maybe(rng, 0.75):
        vatreg = t1.strip()[:20]
    elif _maybe(rng, 0.5):
        vatreg = _alnum(rng, rng.randint(6, 20))

    cust_name_short = name1[:80]

    row = dict(
        Client=client,
        Customer=cust,
        CustomerName=cust_name_short,
        CustomerFullName=full_name[:220],
        CreatedByUser=cre_user[:12],
        CreationDate=cre_date,
        AddressId=addr,
        CustomerClassification=kla,
        VatRegistration=vatreg[:20],
        CustomerAccountGroup=account_group,
        AuthorizationGroup=auth,
        DeliveryIsBlocked=del_block,
        PostingIsBlocked=post_block,
        BillingIsBlockedForCustomer=bill_block,
        OrderIsBlockedForCustomer=ord_block,
        InternationalAllocationNumber1=iln1,
        IsOneTimeAccount=one_time,
        TaxJurisdiction=txjcd,
        Industry=industry,
        TaxNumberType=tt,
        TaxNumber1=t1[:16],
        TaxNumber2=t2[:11],
        TaxNumber3=t3[:18],
        TaxNumber4=t4[:18],
        TaxNumber5=t5[:60],
        TaxNumber6=t6[:20],
        CustomerCorporateGroup=corp,
        Supplier=supplier,
        NielsenRegion=nielsen,
        IndustryCode1=ic[0],
        IndustryCode2=ic[1],
        IndustryCode3=ic[2],
        IndustryCode4=ic[3],
        IndustryCode5=ic[4],
        Country=country,
        OrganizationBpName1=name1,
        OrganizationBpName2=name2,
        CityName=city,
        PostalCode=postal[:10],
        StreetName=street,
        SortField=sort_key,
        FaxNumber=fax,
        BrSuframaCode=(
            "".join(rng.choice(string.digits) for _ in range(9))[:9] if country == "BR" and _maybe(rng, 0.15) else ""
        ),
        Region=region[:3],
        TelephoneNumber1=phone1[:16],
        TelephoneNumber2=phone2[:16],
        AlternativePayerAccount=alt_payer,
        DataMediumExchangeIndicator=dmei[:1],
        VatLiability=vliab[:1],
        IsBusinessPurposeCompleted=bus_done[:1],
        ResponsibleType=resp_tp[:2],
        FiscalAddress=fiscal_addr,
        NfPartnerIsNaturalPerson=nf_nat[:1],
        DeletionIndicator=del_ind[:1],
        Language=lang[:1],
        TradingPartner=tp,
        DeliveryDateTypeRule=deliv_rule[:1],
        ExpressTrainStationName=bahn_exp,
        TrainStationName=bahn,
        InternationalAllocationNumber2=iln2,
        InternationalAllocationNumber3=iln3,
        CityCode=city_code[:4],
        County=county[:3],
        CustomerHasUnloadingPoint=unloading[:1],
        CustomerWorkingTimeCalendar=work_cal[:2],
        IsCompetitor=competitor[:1],
        TaxInvoiceRepresentativeName=repr_name,
        BusinessType=biz_type,
        IndustryType=ind_type,
        TwCollvBillingIsSupported=tw[:1],
        AlternativePayeeIsAllowed=alt_pay_allow[:1],
        FreeDefinedAttribute01=free[0][:2],
        FreeDefinedAttribute02=free[1][:2],
        FreeDefinedAttribute03=free[2][:2],
        FreeDefinedAttribute04=free[3][:2],
        FreeDefinedAttribute05=free[4][:2],
        FreeDefinedAttribute06=free[5][:3],
        FreeDefinedAttribute07=free[6][:3],
        FreeDefinedAttribute08=free[7][:3],
        FreeDefinedAttribute09=free[8][:3],
        FreeDefinedAttribute10=free[9][:3],
    )
    return row


def _customer_row_stream(ctx: FakeContext, args: argparse.Namespace, n: int):
    rng = ctx.rng
    offset = rng.randint(0, 50_000) if args.seed is None else 0
    start = args.start_customer + offset
    for i in range(n):
        yield generate_row(ctx, start + i)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera CSV sintetico tipo I_Customer.")
    repo = Path(__file__).resolve().parent.parent
    parser.add_argument(
        "--output",
        type=Path,
        default=repo / "data" / "I_Customer.csv",
        help="Caminho do CSV de saida.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Linhas sem header (opcional). Fora de --quick: ajustado ao intervalo "
            f"[{I_CUSTOMER_MIN_ROWS}, {I_CUSTOMER_MAX_ROWS}]; sem este argumento usa {I_CUSTOMER_DEFAULT_ROWS}."
        ),
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help=f"Teste rapido: gera exatamente {I_CUSTOMER_QUICK_TEST_ROWS} linhas (ignora faixa 120k-150k).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=SYNTHETIC_MASTER_SEED,
        help="Seed para reproducibilidade (repo: sap_synthetic_masters.SYNTHETIC_MASTER_SEED).",
    )
    parser.add_argument(
        "--start-customer",
        type=int,
        default=DEFAULT_START_CUSTOMER_NUMBER,
        help="Valor numerico inicial para campo Customer (preenchido com zeros a esquerda, 10 posicoes).",
    )
    args = parser.parse_args()

    if args.quick:
        if args.rows is not None:
            print("Aviso: --quick ignora --rows (usa volume de teste fixo).", file=sys.stderr)
        args.rows = I_CUSTOMER_QUICK_TEST_ROWS
    else:
        requested = args.rows if args.rows is not None else I_CUSTOMER_DEFAULT_ROWS
        if requested < I_CUSTOMER_MIN_ROWS:
            print(
                f"Aviso: --rows={requested} abaixo do minimo; ajustado a {I_CUSTOMER_MIN_ROWS}.",
                file=sys.stderr,
            )
        if requested > I_CUSTOMER_MAX_ROWS:
            print(
                f"Aviso: --rows={requested} acima do maximo; ajustado a {I_CUSTOMER_MAX_ROWS}.",
                file=sys.stderr,
            )
        args.rows = max(I_CUSTOMER_MIN_ROWS, min(requested, I_CUSTOMER_MAX_ROWS))

    args.output.parent.mkdir(parents=True, exist_ok=True)

    def discover_output_columns() -> list[str]:
        seen = dict.fromkeys(COLUMNS, False)
        ctx_disc = _build_fakers(args.seed)
        for row in _customer_row_stream(ctx_disc, args, args.rows):
            for c in COLUMNS:
                if seen[c]:
                    continue
                if csv_cell_has_semantic_value(row.get(c)):
                    seen[c] = True
        return [c for c in COLUMNS if seen[c]]

    out_cols = discover_output_columns()

    ctx_write = _build_fakers(args.seed)

    try:
        from tqdm import tqdm

        row_iter = tqdm(
            _customer_row_stream(ctx_write, args, args.rows),
            total=args.rows,
            desc="I_Customer",
            unit="rows",
        )
    except ImportError:
        row_iter = _customer_row_stream(ctx_write, args, args.rows)

    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_cols)
        writer.writeheader()
        for row in row_iter:
            writer.writerow({k: row[k] for k in out_cols})

    print(f"Escrito {args.rows} linhas ({len(out_cols)} colunas) em {args.output.resolve()}")


if __name__ == "__main__":
    main()
