from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm

COLUNAS = [
    "CompanyCode",
    "Plant",
    "Material",
    "FiscalYear",
    "FiscalPeriod",
    "TipoMaterial",
    "TipoMaterialText",
    "PlantName",
    "ContaContabil",
    "ContaContabilText",
    "ProfitCenter",
    "CompanyCodeCurrency",
    "BaseUnit",
    "EstoqueQuantidade",
    "EstoqueValorTotal",
    "PrecoUnitario_Oficial",
]

DOMINIOS = {
    "CompanyCode": ["BR01", "US10", "DE10", "FR01", "UK01"],
    "CompanyCodeCurrency": ["BRL", "USD", "EUR", "GBP"],
    "Plant": ["P001", "P002", "P003", "P004"],
}

# MTART / texto (valorização inventário / MM)
TIPO_MATERIAL_TO_TEXT = {
    "ROH": "Materia Prima",
    "FERT": "Produto Acabado",
    "HALB": "Semi-Acabado",
    "HAWA": "Mercadoria Revenda",
}
TIPOS_MATERIAL = list(TIPO_MATERIAL_TO_TEXT.keys())

# Werks / nome do centro
PLANT_TO_NAME = {
    "P001": "Fabrica Matriz SP",
    "P002": "Centro Distribuicao RJ",
    "P003": "Planta Exportacao SC",
    "P004": "Filial Norte",
}

# Contas de estoque (Ativo — apenas uso em inventário)
CONTA_CONTABIL_TO_TEXT = {
    "130100": "Estoque Prod. Acabado",
    "130200": "Estoque Matéria Prima",
    "130300": "Estoque Merc. Revenda",
}

# IDs de material para estoque
MATERIAIS_STK = [
    "MAT-1001",
    "MAT-1002",
    "MAT-1003",
    "MAT-1004",
    "MAT-1005",
    "RM-001",
    "RM-002",
    "RM-003",
    "HALB-2010",
    "HALB-2020",
    "FERT-3001",
    "FERT-3002",
    "HAWA-4001",
    "SKU-STK-01",
    "SKU-STK-02",
]

PROFIT_CENTERS = ["PC-1000", "PC-2000", "PC-3000"]

BASE_UNITS = ["KG", "PC", "L", "TON", "M"]


def _nova_linha(r: np.random.Generator) -> dict[str, object]:
    plant = str(r.choice(DOMINIOS["Plant"]))
    conta = str(r.choice(list(CONTA_CONTABIL_TO_TEXT.keys())))
    tipo_material = str(r.choice(TIPOS_MATERIAL))
    material = str(r.choice(MATERIAIS_STK))

    estoque_quantidade = float(np.round(r.uniform(10, 5000), 3))
    preco_unitario_oficial = float(np.round(r.uniform(5, 1500), 3))
    estoque_valor_total = round(estoque_quantidade * preco_unitario_oficial, 2)

    return {
        "CompanyCode": str(r.choice(DOMINIOS["CompanyCode"])),
        "Plant": plant,
        "Material": material,
        "FiscalYear": int(r.integers(2023, 2026)),
        "FiscalPeriod": int(r.integers(1, 13)),
        "TipoMaterial": tipo_material,
        "TipoMaterialText": TIPO_MATERIAL_TO_TEXT[tipo_material],
        "PlantName": PLANT_TO_NAME[plant],
        "ContaContabil": conta,
        "ContaContabilText": CONTA_CONTABIL_TO_TEXT[conta],
        "ProfitCenter": str(r.choice(PROFIT_CENTERS)),
        "CompanyCodeCurrency": str(r.choice(DOMINIOS["CompanyCodeCurrency"])),
        "BaseUnit": str(r.choice(BASE_UNITS)),
        "EstoqueQuantidade": estoque_quantidade,
        "EstoqueValorTotal": estoque_valor_total,
        "PrecoUnitario_Oficial": preco_unitario_oficial,
    }


def gerar_custo_material_stk(linhas: int = 80_000, semente: int = 42, diretorio_saida: str = "data") -> Path:
    r = np.random.default_rng(semente)
    registros = []
    for _ in tqdm(range(linhas), desc="Gerando Custo_Material_STK", unit="linhas"):
        linha = _nova_linha(r)
        registros.append({c: linha[c] for c in COLUNAS})

    df = pd.DataFrame(registros, columns=COLUNAS)
    # Evita coerção para int nas contas (ex.: 130100) ao materializar o DataFrame
    df["ContaContabil"] = df["ContaContabil"].astype(str)

    p = Path(diretorio_saida) / "Custo_Material_STK.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)
    return p


if __name__ == "__main__":
    print("[ZI_CUSTO_MATERIAL_STK] Iniciando geracao do CSV...")
    caminho_csv = gerar_custo_material_stk()
    print(f"[ZI_CUSTO_MATERIAL_STK] Geracao concluida com sucesso: {caminho_csv.resolve()}")
