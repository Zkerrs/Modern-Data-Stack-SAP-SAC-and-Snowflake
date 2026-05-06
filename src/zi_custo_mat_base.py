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
    "QtdBruta",
    "ValorTotalCalculado",
    "PrecoUnitarioBruto",
]

DOMINIOS = {
    "CompanyCode": ["BR01", "US10", "DE10", "FR01", "UK01"],
    "CompanyCodeCurrency": ["BRL", "USD", "EUR", "GBP"],
    "Plant": ["P001", "P002", "P003", "P004"],
}

# MTART / descrição (domínio SAP)
TIPO_MATERIAL_TO_TEXT = {
    "ROH": "Materia Prima",
    "HALB": "Produto Semi-Acabado",
    "FERT": "Produto Acabado",
    "HAWA": "Mercadoria de Revenda",
}
TIPOS_MATERIAL = list(TIPO_MATERIAL_TO_TEXT.keys())

# MEINS (unidade base)
BASE_UNITS = ["KG", "PC", "L", "TON", "M"]

# Werks / nome do centro
PLANT_TO_NAME = {
    "P001": "Fabrica Matriz SP",
    "P002": "Filial RJ",
    "P003": "Fabrica Berlim",
    "P004": "Centro Distribuicao US",
}

# Conta contábil / texto
CONTA_TO_TEXT = {
    "130100": "Conta de Estoque Materiais",
    "510100": "Custo de Mercadoria Vendida (CMV)",
    "510110": "Consumo de Materia Prima",
}

# Materiais (ID produto), lista fixa alfa-numérica
MATERIAIS_FIXOS = [
    "MAT-1001",
    "MAT-1002",
    "MAT-1003",
    "MAT-1004",
    "MAT-1005",
    "MAT-1010",
    "MAT-1015",
    "MAT-1020",
    "RM-005",
    "RM-012",
    "RM-023",
    "RM-045",
    "HALB-2001",
    "HALB-2002",
    "FERT-3001",
    "FERT-3002",
    "FERT-3003",
    "HAWA-4001",
    "MP-ALPHA",
    "MP-BETA",
    "SKU-8891",
]

# Centro de lucro (padrão típico SAP)
PROFIT_CENTERS = ["PC-1000", "PC-2000", "PC-3000"]


def _nova_linha(r: np.random.Generator) -> dict[str, object]:
    plant = str(r.choice(DOMINIOS["Plant"]))
    conta = str(r.choice(list(CONTA_TO_TEXT.keys())))
    tipo_mat = str(r.choice(TIPOS_MATERIAL))
    material = str(r.choice(MATERIAIS_FIXOS))

    qtd_bruta = float(np.round(r.uniform(1, 5000), 3))
    preco_unitario_bruto = float(np.round(r.uniform(1, 5000), 3))
    valor_total_calculado = round(qtd_bruta * preco_unitario_bruto, 2)

    return {
        "CompanyCode": str(r.choice(DOMINIOS["CompanyCode"])),
        "Plant": plant,
        "Material": material,
        "FiscalYear": int(r.integers(2023, 2026)),
        "FiscalPeriod": int(r.integers(1, 13)),
        "TipoMaterial": tipo_mat,
        "TipoMaterialText": TIPO_MATERIAL_TO_TEXT[tipo_mat],
        "PlantName": PLANT_TO_NAME[plant],
        "ContaContabil": conta,
        "ContaContabilText": CONTA_TO_TEXT[conta],
        "ProfitCenter": str(r.choice(PROFIT_CENTERS)),
        "CompanyCodeCurrency": str(r.choice(DOMINIOS["CompanyCodeCurrency"])),
        "BaseUnit": str(r.choice(BASE_UNITS)),
        "QtdBruta": qtd_bruta,
        "ValorTotalCalculado": valor_total_calculado,
        "PrecoUnitarioBruto": preco_unitario_bruto,
    }


def gerar_custo_mat_base(linhas: int = 120_000, semente: int = 42, diretorio_saida: str = "data") -> Path:
    r = np.random.default_rng(semente)
    registros = []
    for _ in tqdm(range(linhas), desc="Gerando Custo_Mat_Base", unit="linhas"):
        row = _nova_linha(r)
        registros.append({c: row[c] for c in COLUNAS})
    df = pd.DataFrame(registros, columns=COLUNAS)
    p = Path(diretorio_saida) / "Custo_Mat_Base.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)
    return p


if __name__ == "__main__":
    print("[ZI_CUSTO_MAT_BASE] Iniciando geracao do CSV...")
    caminho_csv = gerar_custo_mat_base()
    print(f"[ZI_CUSTO_MAT_BASE] Geracao concluida com sucesso: {caminho_csv.resolve()}")
