"""
CSV sintetico I_ProductType: espelho completo para tipo de material no padrao I_*.

Mantem `Client` na primeira coluna e inclui atributos tecnicos/customizing
tipicos de Product Type (material type), alem de texto.

Uso:
  python src/generate_i_producttype_csv.py --output data/I_ProductType.csv
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

from sap_synthetic_masters import (
    I_PRODUCTTYPE_DEFAULT_ROWS,
    I_PRODUCTTYPE_MAX_ROWS,
    I_PRODUCTTYPE_MIN_ROWS,
    I_PRODUCTTYPE_QUICK_TEST_ROWS,
    MASTER_CLIENT_IDS,
    MASTER_PRODUCT_TYPES,
    SYNTHETIC_MASTER_SEED,
    column_order_excluding_always_empty,
)

# Ordem em PascalCase, com mandante primeiro.
PRODUCTTYPE_COLUMNS = [
    "Client",
    "ProductType",
    "ProductTypeName",
    "Language",
    "MaterialTypeCategory",
    "IndustrySector",
    "MaterialTypeRefProductType",
    "NumberRangeGroup",
    "ExternalNumberRangeIsAllowed",
    "InternalNumberRangeIsAllowed",
    "QuantityIsUpdated",
    "ValueIsUpdated",
    "BatchManagementIsRequired",
    "SplitValuationIsAllowed",
    "NegativeStocksAreAllowed",
    "MaterialLedgerIsActivated",
    "PriceControl",
    "AccountCategoryReference",
    "SerialNumberProfile",
    "DefaultUnitOfMeasure",
    "ProductGroup",
    "CreatedByUser",
    "CreationDate",
    "LastChangedByUser",
    "LastChangeDate",
    "IsMarkedForDeletion",
]

_PRODUCT_TYPE_NAMES: dict[str, str] = {
    "FERT": "Finished Product",
    "HALB": "Semi-Finished Product",
    "ROH": "Raw Material",
    "HAWA": "Trading Goods",
    "NLAG": "Non-Stock Material",
    "DIEN": "Service",
    "ERSA": "Spare Part",
}


def _pad(value: str, max_len: int) -> str:
    return (value or "")[:max_len]


def _x(flag: bool) -> str:
    return "X" if flag else ""


def _type_profile(product_type: str, rng: random.Random) -> dict[str, str]:
    # Perfil sintetico por MTART para manter dados verossimeis.
    if product_type == "FERT":
        return {
            "MaterialTypeCategory": "01",
            "IndustrySector": "M",
            "MaterialTypeRefProductType": "",
            "NumberRangeGroup": "01",
            "ExternalNumberRangeIsAllowed": "",
            "InternalNumberRangeIsAllowed": "X",
            "QuantityIsUpdated": "X",
            "ValueIsUpdated": "X",
            "BatchManagementIsRequired": _x(rng.random() < 0.45),
            "SplitValuationIsAllowed": "X",
            "NegativeStocksAreAllowed": "",
            "MaterialLedgerIsActivated": "X",
            "PriceControl": rng.choice(["S", "V"]),
            "AccountCategoryReference": "0001",
            "SerialNumberProfile": rng.choice(["SER1", "ZSER", ""]),
            "DefaultUnitOfMeasure": rng.choice(["EA", "PC", "CS"]),
            "ProductGroup": rng.choice(["Z001", "Z010", "ZMAT"]),
        }
    if product_type == "HALB":
        return {
            "MaterialTypeCategory": "02",
            "IndustrySector": "M",
            "MaterialTypeRefProductType": "FERT",
            "NumberRangeGroup": "02",
            "ExternalNumberRangeIsAllowed": "",
            "InternalNumberRangeIsAllowed": "X",
            "QuantityIsUpdated": "X",
            "ValueIsUpdated": "X",
            "BatchManagementIsRequired": _x(rng.random() < 0.55),
            "SplitValuationIsAllowed": "X",
            "NegativeStocksAreAllowed": "",
            "MaterialLedgerIsActivated": "X",
            "PriceControl": rng.choice(["S", "V"]),
            "AccountCategoryReference": "0002",
            "SerialNumberProfile": rng.choice(["SER1", "ZSER", ""]),
            "DefaultUnitOfMeasure": rng.choice(["EA", "KG", "M"]),
            "ProductGroup": rng.choice(["Z002", "Z020", "ZMAT"]),
        }
    if product_type == "ROH":
        return {
            "MaterialTypeCategory": "03",
            "IndustrySector": "M",
            "MaterialTypeRefProductType": "",
            "NumberRangeGroup": "03",
            "ExternalNumberRangeIsAllowed": "X",
            "InternalNumberRangeIsAllowed": "X",
            "QuantityIsUpdated": "X",
            "ValueIsUpdated": "X",
            "BatchManagementIsRequired": _x(rng.random() < 0.65),
            "SplitValuationIsAllowed": "X",
            "NegativeStocksAreAllowed": "",
            "MaterialLedgerIsActivated": "X",
            "PriceControl": "V",
            "AccountCategoryReference": "0003",
            "SerialNumberProfile": "",
            "DefaultUnitOfMeasure": rng.choice(["KG", "G", "L", "M"]),
            "ProductGroup": rng.choice(["Z020", "Z030", "ZMAT"]),
        }
    if product_type == "HAWA":
        return {
            "MaterialTypeCategory": "04",
            "IndustrySector": "A",
            "MaterialTypeRefProductType": "",
            "NumberRangeGroup": "04",
            "ExternalNumberRangeIsAllowed": "X",
            "InternalNumberRangeIsAllowed": "X",
            "QuantityIsUpdated": "X",
            "ValueIsUpdated": "X",
            "BatchManagementIsRequired": _x(rng.random() < 0.2),
            "SplitValuationIsAllowed": "",
            "NegativeStocksAreAllowed": _x(rng.random() < 0.12),
            "MaterialLedgerIsActivated": "X",
            "PriceControl": "V",
            "AccountCategoryReference": "0004",
            "SerialNumberProfile": rng.choice(["SER1", ""]),
            "DefaultUnitOfMeasure": rng.choice(["EA", "PC"]),
            "ProductGroup": rng.choice(["Z001", "Z002", "Z010"]),
        }
    if product_type == "NLAG":
        return {
            "MaterialTypeCategory": "05",
            "IndustrySector": "M",
            "MaterialTypeRefProductType": "",
            "NumberRangeGroup": "05",
            "ExternalNumberRangeIsAllowed": "X",
            "InternalNumberRangeIsAllowed": "X",
            "QuantityIsUpdated": "",
            "ValueIsUpdated": "",
            "BatchManagementIsRequired": "",
            "SplitValuationIsAllowed": "",
            "NegativeStocksAreAllowed": "",
            "MaterialLedgerIsActivated": "",
            "PriceControl": "",
            "AccountCategoryReference": "0005",
            "SerialNumberProfile": "",
            "DefaultUnitOfMeasure": rng.choice(["EA", "PC"]),
            "ProductGroup": rng.choice(["Z001", "Z010", "ZSRV"]),
        }
    if product_type == "DIEN":
        return {
            "MaterialTypeCategory": "06",
            "IndustrySector": "P",
            "MaterialTypeRefProductType": "",
            "NumberRangeGroup": "06",
            "ExternalNumberRangeIsAllowed": "X",
            "InternalNumberRangeIsAllowed": "X",
            "QuantityIsUpdated": "",
            "ValueIsUpdated": "X",
            "BatchManagementIsRequired": "",
            "SplitValuationIsAllowed": "",
            "NegativeStocksAreAllowed": "",
            "MaterialLedgerIsActivated": "",
            "PriceControl": "V",
            "AccountCategoryReference": "0006",
            "SerialNumberProfile": "",
            "DefaultUnitOfMeasure": "EA",
            "ProductGroup": "ZSRV",
        }
    return {
        "MaterialTypeCategory": "07",
        "IndustrySector": "M",
        "MaterialTypeRefProductType": "ROH",
        "NumberRangeGroup": "07",
        "ExternalNumberRangeIsAllowed": "X",
        "InternalNumberRangeIsAllowed": "X",
        "QuantityIsUpdated": "X",
        "ValueIsUpdated": "X",
        "BatchManagementIsRequired": _x(rng.random() < 0.35),
        "SplitValuationIsAllowed": "X",
        "NegativeStocksAreAllowed": "",
        "MaterialLedgerIsActivated": "X",
        "PriceControl": "V",
        "AccountCategoryReference": "0007",
        "SerialNumberProfile": rng.choice(["SER1", ""]),
        "DefaultUnitOfMeasure": rng.choice(["EA", "PC"]),
        "ProductGroup": rng.choice(["Z001", "Z002", "ZMAT"]),
    }


def build_row(product_type: str, client: str, idx: int, rng: random.Random) -> dict[str, str]:
    profile = _type_profile(product_type, rng)
    lang = ("E", "P", "D", "F")[idx % 4]
    creation_date = f"{2018 + (idx % 7):04d}{(idx % 12) + 1:02d}{((idx % 27) + 1):02d}"
    change_date = f"{2023 + (idx % 3):04d}{((idx + 3) % 12) + 1:02d}{((idx + 10) % 27) + 1:02d}"
    return {
        "Client": _pad(client, 3),
        "ProductType": _pad(product_type, 4),
        "ProductTypeName": _pad(_PRODUCT_TYPE_NAMES.get(product_type, product_type), 40),
        "Language": lang,
        "MaterialTypeCategory": _pad(profile["MaterialTypeCategory"], 2),
        "IndustrySector": _pad(profile["IndustrySector"], 1),
        "MaterialTypeRefProductType": _pad(profile["MaterialTypeRefProductType"], 4),
        "NumberRangeGroup": _pad(profile["NumberRangeGroup"], 2),
        "ExternalNumberRangeIsAllowed": _pad(profile["ExternalNumberRangeIsAllowed"], 1),
        "InternalNumberRangeIsAllowed": _pad(profile["InternalNumberRangeIsAllowed"], 1),
        "QuantityIsUpdated": _pad(profile["QuantityIsUpdated"], 1),
        "ValueIsUpdated": _pad(profile["ValueIsUpdated"], 1),
        "BatchManagementIsRequired": _pad(profile["BatchManagementIsRequired"], 1),
        "SplitValuationIsAllowed": _pad(profile["SplitValuationIsAllowed"], 1),
        "NegativeStocksAreAllowed": _pad(profile["NegativeStocksAreAllowed"], 1),
        "MaterialLedgerIsActivated": _pad(profile["MaterialLedgerIsActivated"], 1),
        "PriceControl": _pad(profile["PriceControl"], 1),
        "AccountCategoryReference": _pad(profile["AccountCategoryReference"], 4),
        "SerialNumberProfile": _pad(profile["SerialNumberProfile"], 4),
        "DefaultUnitOfMeasure": _pad(profile["DefaultUnitOfMeasure"], 3),
        "ProductGroup": _pad(profile["ProductGroup"], 9),
        "CreatedByUser": _pad(("MM_CUSTOM", "MDG_BATCH", "CB9980520010")[idx % 3], 12),
        "CreationDate": creation_date,
        "LastChangedByUser": _pad(("MM_CUSTOM", "MDG_BATCH", "CB9980520020")[idx % 3], 12),
        "LastChangeDate": change_date,
        "IsMarkedForDeletion": "X" if (idx % 7001 == 0 and idx > 0) else "",
    }


def main() -> None:
    repo = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Gera I_ProductType.csv a partir dos mestres.")
    parser.add_argument("--output", type=Path, default=repo / "data" / "I_ProductType.csv")
    parser.add_argument(
        "--rows",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Linhas sem header. Fora de --quick: ajustado ao intervalo "
            f"[{I_PRODUCTTYPE_MIN_ROWS}, {I_PRODUCTTYPE_MAX_ROWS}]; sem argumento usa {I_PRODUCTTYPE_DEFAULT_ROWS}."
        ),
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help=f"Teste rapido ({I_PRODUCTTYPE_QUICK_TEST_ROWS} linhas).",
    )
    parser.add_argument("--seed", type=int, default=SYNTHETIC_MASTER_SEED)
    parser.add_argument(
        "--client",
        type=str,
        default="",
        help="Mandante fixo (3 chars). Vazio = rotacao MASTER_CLIENT_IDS por linha.",
    )
    args = parser.parse_args()

    if args.quick:
        if args.rows is not None:
            print("Aviso: --quick ignora --rows.", file=sys.stderr)
        args.rows = I_PRODUCTTYPE_QUICK_TEST_ROWS
    else:
        requested = args.rows if args.rows is not None else I_PRODUCTTYPE_DEFAULT_ROWS
        if requested < I_PRODUCTTYPE_MIN_ROWS:
            print(
                f"Aviso: --rows={requested} abaixo do minimo; ajustado a {I_PRODUCTTYPE_MIN_ROWS}.",
                file=sys.stderr,
            )
        if requested > I_PRODUCTTYPE_MAX_ROWS:
            print(
                f"Aviso: --rows={requested} acima do maximo; ajustado a {I_PRODUCTTYPE_MAX_ROWS}.",
                file=sys.stderr,
            )
        args.rows = max(I_PRODUCTTYPE_MIN_ROWS, min(requested, I_PRODUCTTYPE_MAX_ROWS))

    rng = random.Random(args.seed)

    args.output.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for i in range(args.rows):
        pt = MASTER_PRODUCT_TYPES[i % len(MASTER_PRODUCT_TYPES)]
        cl = args.client.strip()[:3] if args.client else MASTER_CLIENT_IDS[i % len(MASTER_CLIENT_IDS)]
        rows.append(build_row(pt, cl, i, rng))

    out_cols = column_order_excluding_always_empty(PRODUCTTYPE_COLUMNS, rows)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_cols)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in out_cols})

    print(f"Escrito {args.rows} linhas ({len(out_cols)} colunas) em {args.output.resolve()}")


if __name__ == "__main__":
    main()
