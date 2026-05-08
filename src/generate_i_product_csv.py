"""
CSV sintetico espelho da view standard `I_Product` (material / OData A_ProductType).

Inclui texto de `A_ProductDescriptionType` (ProductDescription, Language). Primeira coluna `Client`.
Lista de colunas: foco em campos centrais do cabecalho do material; demais campos OData ficam de fora
propositalmente para manter extracao leve (como em muitos projetos reais).

Volume fora de --quick: faixa propria de material master (ver `sap_synthetic_masters.I_PRODUCT_*`),
nao 120k — alinhado a cardinalidade tipica MDG/MM.

Uso:
  python src/generate_i_product_csv.py [--rows N] --output data/I_Product.csv
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
    I_PRODUCT_DEFAULT_ROWS,
    I_PRODUCT_MAX_ROWS,
    I_PRODUCT_MIN_ROWS,
    I_PRODUCT_QUICK_TEST_ROWS,
    MASTER_CLIENT_IDS,
    MASTER_COMPANY_CODES,
    MASTER_PLANTS,
    MASTER_PRODUCT_GROUPS,
    MASTER_PRODUCT_TYPES,
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

_COMPANY_ORIGIN: dict[str, str] = {
    "BR01": "BR",
    "US10": "US",
    "DE10": "DE",
    "FR01": "FR",
    "UK01": "GB",
}

_PRODUCT_COLUMNS: list[str] = [
    "Client",
    "Product",
    "ProductDescription",
    "Language",
    "ProductType",
    "BaseUnit",
    "PurchaseOrderQuantityUnit",
    "PreferredUnitOfMeasure",
    "ProductGroup",
    "ProductHierarchy",
    "Division",
    "IndustrySector",
    "ItemCategoryGroup",
    "CountryOfOrigin",
    "NetWeight",
    "GrossWeight",
    "WeightUnit",
    "MaterialVolume",
    "VolumeUnit",
    "ValidityStartDate",
    "CreatedByUser",
    "CreationDate",
    "LastChangedByUser",
    "LastChangeDate",
    "AuthorizationGroup",
    "CrossPlantStatus",
    "Brand",
    "ProductManufacturerNumber",
    "WarehouseProductGroup",
    "WarehouseStorageCondition",
    "ProcurementRule",
    "IsMarkedForDeletion",
    "IsBatchManagementRequired",
    "ProductIsConfigurable",
    "QltyMgmtInProcmtIsActive",
    "QualityInspectionGroup",
    "SerialNumberProfile",
    "SizeOrDimensionText",
]

_INDUSTRY_SECTORS: tuple[str, ...] = ("M", "P", "A", "C", "L", "O")
_ITEM_CAT_GROUPS: tuple[str, ...] = ("NORM", "LUMF", "BANS", "LEER", "VERP")
_DIVISIONS: tuple[str, ...] = ("00", "10", "20", "30", "40")

_BASE_MATERIAL_TERMS_BY_TYPE: dict[str, tuple[str, ...]] = {
    "ROH": (
        "Aco Carbono",
        "Aco Inox",
        "Aluminio",
        "Cobre",
        "Latão",
        "Polietileno",
        "Polipropileno",
        "Resina Epoxi",
        "Papel Kraft",
        "Papel Reciclado",
        "Celulose",
        "Borracha Nitrilica",
        "Tecido Tecnico",
        "Vidro Temperado",
        "Granulado PVC",
    ),
    "HALB": (
        "Chapa de Aco",
        "Perfil Metalico",
        "Bobina de Papel",
        "Filme Plastico",
        "Tubo de Aluminio",
        "Bloco de Cobre",
        "Placa de Polimero",
        "Painel Laminado",
        "Composto Quimico",
        "Placa Tecnica",
    ),
    "FERT": (
        "Painel Metalico",
        "Embalagem Plastica",
        "Caderno Corporativo",
        "Garrafa PET",
        "Caixa de Papel",
        "Suporte de Aco",
        "Conector de Cobre",
        "Modulo Industrial",
        "Kit de Montagem",
        "Componente Eletrico",
        "Bandeja de Aluminio",
    ),
    "HAWA": (
        "Parafuso Galvanizado",
        "Adesivo Industrial",
        "Fita Tecnica",
        "Manta Plastica",
        "Papel Cartao",
        "Valvula de Metal",
        "Rolamento",
        "Conector Universal",
        "Filtro de Ar",
    ),
    "NLAG": (
        "Material de Escritorio",
        "Etiqueta Adesiva",
        "Caixa Arquivo",
        "Papel Sulfite",
        "Pano de Limpeza",
        "Insumo de Apoio",
    ),
    "DIEN": (
        "Servico de Corte",
        "Servico de Pintura",
        "Servico de Embalagem",
        "Servico de Inspecao",
        "Servico de Montagem",
        "Servico de Transporte",
    ),
    "ERSA": (
        "Peca de Reposicao",
        "Engrenagem Reserva",
        "Sensor Reserva",
        "Kit de Vedacao",
        "Rolamento Reserva",
        "Chave de Manutencao",
    ),
}

_MATERIAL_QUALIFIERS: tuple[str, ...] = (
    "Industrial",
    "Premium",
    "Standard",
    "Reforcado",
    "Leve",
    "Flexivel",
    "Alta Densidade",
    "Baixa Densidade",
    "Tecnico",
    "Automotivo",
    "Alimenticio",
    "Farmaceutico",
)


def _pad(s: str | None, max_len: int) -> str:
    if s is None:
        return ""
    return str(s)[:max_len]


def _normalize_text(s: str) -> str:
    t = re.sub(r"\([^)]*\)", " ", s or "")
    t = t.replace(",", " ").replace(";", " ").replace("/", " ")
    return " ".join(t.split()).strip()


def _sample_date(rng: random.Random) -> str:
    start = datetime(2014, 1, 1)
    end = datetime(2026, 5, 1)
    day = start + timedelta(days=rng.randint(0, (end - start).days))
    return day.strftime("%Y%m%d")


def _bool_x(v: bool) -> str:
    return "X" if v else ""


def _product_number(idx: int) -> str:
    n = 5_010_000_100 + (idx * 137) % 94_989_900
    return str(n).zfill(18)[:40]


def _hierarchy(rng: random.Random) -> str:
    parts = [f"{rng.randint(1, 9):03d}" for _ in range(6)]
    return "".join(parts)[:18]


def _material_description(ptype: str, idx: int, plant: str, rng: random.Random) -> str:
    base_terms = _BASE_MATERIAL_TERMS_BY_TYPE.get(ptype, ("Material Generico",))
    base = rng.choice(base_terms)
    qual = rng.choice(_MATERIAL_QUALIFIERS)
    spec = f"{rng.randint(1, 99):02d}{rng.choice(('A', 'B', 'C', 'D'))}"
    text = f"{base} {qual} {spec} {plant}"
    return _pad(_normalize_text(text), 40)


def build_row(company: dict[str, str], client: str, idx: int, rng: random.Random) -> dict[str, str]:
    bukrs = company["CompanyCode"]
    lang2 = _COMPANY_LANG2.get(bukrs, "EN")
    origin = _COMPANY_ORIGIN.get(bukrs, "US")
    locales = {"BR": "pt_BR", "US": "en_US", "DE": "de_DE", "FR": "fr_FR", "GB": "en_GB"}
    fk = Faker(locales.get(origin, "en_US"))
    fk.seed_instance(int(rng.getrandbits(32)) ^ SYNTHETIC_MASTER_SEED ^ (idx * 41))

    matnr = _product_number(idx)
    plant = MASTER_PLANTS[idx % len(MASTER_PLANTS)]
    ptype = MASTER_PRODUCT_TYPES[idx % len(MASTER_PRODUCT_TYPES)]
    desc = _material_description(ptype, idx, plant, rng)

    if ptype in {"DIEN"}:
        base_u, po_u = "EA", "EA"
    elif ptype in {"FERT", "HALB"}:
        base_u = rng.choice(["EA", "PC", "CS", "PAL"])
        po_u = rng.choice([base_u, "EA", "CS"])
    else:
        base_u = rng.choice(["KG", "G", "L", "EA", "M", "M2"])
        po_u = rng.choice([base_u, "KG", "EA"])

    net_w = round(rng.uniform(0.001, 420.0), 3)
    gross_w = round(net_w * rng.uniform(1.0, 1.25), 3) if net_w > 0 else 0.0
    vol = round(rng.uniform(0.0, 2.5), 3) if rng.random() > 0.35 else 0.0

    vol_unit = ""
    if vol > 0:
        vol_unit = rng.choice(["M3", "CDM", "L"])

    wu = "KG" if base_u in {"KG", "G", "L"} else rng.choice(["KG", "G", "LB", ""])

    xf_del = rng.random() < 0.02
    xf_batch = rng.random() < 0.22 and ptype in {"ROH", "HALB", "FERT", "HAWA"}
    xf_cfg = rng.random() < 0.05
    xf_qm = rng.random() < 0.18

    brand_codes = ("ZBX1", "ZBRN", "ORGL", "PLBL", "0001")
    brand = _pad(rng.choice(brand_codes) if rng.random() < 0.35 else "", 4)
    mfr = _pad(f"MFR-{rng.randint(100000, 999999)}" if rng.random() < 0.3 else "", 40)

    return {
        "Client": _pad(client, 3),
        "Product": _pad(matnr, 40),
        "ProductDescription": desc,
        "Language": _pad(lang2, 2),
        "ProductType": _pad(ptype, 4),
        "BaseUnit": _pad(base_u, 3),
        "PurchaseOrderQuantityUnit": _pad(po_u, 3),
        "PreferredUnitOfMeasure": _pad(base_u if rng.random() > 0.5 else po_u, 3),
        "ProductGroup": _pad(MASTER_PRODUCT_GROUPS[idx % len(MASTER_PRODUCT_GROUPS)], 9),
        "ProductHierarchy": _pad(_hierarchy(rng), 18),
        "Division": _pad(rng.choice(_DIVISIONS), 2),
        "IndustrySector": _pad(rng.choice(_INDUSTRY_SECTORS), 1),
        "ItemCategoryGroup": _pad(rng.choice(_ITEM_CAT_GROUPS), 4),
        "CountryOfOrigin": _pad(origin, 3),
        "NetWeight": f"{net_w:.3f}" if net_w > 0 else "",
        "GrossWeight": f"{gross_w:.3f}" if gross_w > 0 and wu else "",
        "WeightUnit": _pad(wu, 3),
        "MaterialVolume": f"{vol:.3f}" if vol > 0 else "",
        "VolumeUnit": vol_unit,
        "ValidityStartDate": _sample_date(rng),
        "CreatedByUser": _pad(rng.choice(["MM_BATCH_01", "MDG_USER08", "CB9980520010"]), 12),
        "CreationDate": _sample_date(rng),
        "LastChangedByUser": _pad(rng.choice(["MM_BATCH_03", "MDG_USER12", "CB9980520020"]), 12),
        "LastChangeDate": _sample_date(rng),
        "AuthorizationGroup": _pad(rng.choice(["", "M001", "M002", "ZMM1"]), 4),
        "CrossPlantStatus": _pad(rng.choice(["", "", "02", "01", "ZL"])[:2], 2),
        "Brand": brand,
        "ProductManufacturerNumber": mfr,
        "WarehouseProductGroup": _pad(rng.choice(["WA01", "WA02", "WHSE", ""]) if rng.random() > 0.4 else "", 4),
        "WarehouseStorageCondition": _pad(rng.choice(["", "02", "04", "Z1"]), 2),
        "ProcurementRule": _pad(rng.choice(["", "", "X", "F"])[:1], 1),
        "IsMarkedForDeletion": _bool_x(xf_del),
        "IsBatchManagementRequired": _bool_x(xf_batch),
        "ProductIsConfigurable": _bool_x(xf_cfg),
        "QltyMgmtInProcmtIsActive": _bool_x(xf_qm),
        "QualityInspectionGroup": _pad(rng.choice(["", "", "ZM01", "QP01"]), 4),
        "SerialNumberProfile": _pad(rng.choice(["", "", "ZSER", "SERIAL1"]) if xf_batch else "", 4),
        "SizeOrDimensionText": _pad(
            f"{rng.randint(1, 500)}mm" if rng.random() < 0.15 else "", 32
        ),
    }


def main() -> None:
    repo = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Gera CSV sintetico tipo I_Product (volume MD).")
    parser.add_argument("--output", type=Path, default=repo / "data" / "I_Product.csv")
    parser.add_argument(
        "--rows",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Linhas sem header. Fora de --quick: ajustado a "
            f"[{I_PRODUCT_MIN_ROWS}, {I_PRODUCT_MAX_ROWS}]; padrao {I_PRODUCT_DEFAULT_ROWS}."
        ),
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help=f"Teste rapido ({I_PRODUCT_QUICK_TEST_ROWS} linhas).",
    )
    parser.add_argument("--seed", type=int, default=SYNTHETIC_MASTER_SEED)
    parser.add_argument(
        "--client",
        type=str,
        default="",
        help="Mandante fixo (3 chars). Vazio = rotacao MASTER_CLIENT_IDS.",
    )
    args = parser.parse_args()

    if args.quick:
        if args.rows is not None:
            print("Aviso: --quick ignora --rows.", file=sys.stderr)
        args.rows = I_PRODUCT_QUICK_TEST_ROWS
    else:
        requested = args.rows if args.rows is not None else I_PRODUCT_DEFAULT_ROWS
        if requested < I_PRODUCT_MIN_ROWS:
            print(
                f"Aviso: --rows={requested} abaixo do minimo MD; ajustado a {I_PRODUCT_MIN_ROWS}.",
                file=sys.stderr,
            )
        if requested > I_PRODUCT_MAX_ROWS:
            print(
                f"Aviso: --rows={requested} acima do maximo MD; ajustado a {I_PRODUCT_MAX_ROWS}.",
                file=sys.stderr,
            )
        args.rows = max(I_PRODUCT_MIN_ROWS, min(requested, I_PRODUCT_MAX_ROWS))

    rng = random.Random(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for i in range(args.rows):
        co = MASTER_COMPANY_CODES[i % len(MASTER_COMPANY_CODES)]
        client = args.client.strip()[:3] if args.client else MASTER_CLIENT_IDS[i % len(MASTER_CLIENT_IDS)]
        rows.append(build_row(co, client, i, rng))

    out_cols = [c for c in _PRODUCT_COLUMNS if any(csv_cell_has_semantic_value(r.get(c)) for r in rows)]
    with args.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in out_cols})

    print(f"Escrito {args.rows} linhas ({len(out_cols)} colunas) em {args.output.resolve()}")


if __name__ == "__main__":
    main()
