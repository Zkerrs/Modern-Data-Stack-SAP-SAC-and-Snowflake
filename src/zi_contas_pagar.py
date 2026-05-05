from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker
from tqdm import tqdm

COLUNAS = [
    "CompanyCode", "DocumentNumber", "DocumentItem", "FiscalYear", "Supplier", "GLAccount", "MandanteCod",
    "Branch", "CompanyName", "VendorName", "DocType", "PostingDate", "DocumentDate", "DueDate", "FiscalPeriod",
    "AmountLocalCurrency", "DebitCredit", "AmountDocumentCurrency", "Currency", "PostingKey", "UMSKZ", "UMSKS",
    "ZUMSK", "DocumentText", "ClearingDocument", "ClearingDate", "CostCenter", "PedidoCompra", "GKONT", "GKOAR",
    "CNPJ", "TipoDespesa", "DocEstorno", "DocumentStatus", "ValorTotalAberto", "ValorTotalCompensado",
]

DOC_TYPES_AP = ("KR", "RE", "KZ")

DOCUMENTOS_TEXTO_AP = (
    "Fatura Fornecedor (KR)",
    "Recebimento Material / Fatura (RE)",
    "Pagamento a Fornecedor (KZ)",
)

EMPRESAS = {
    "BR01": "Brasil Headquarters SA",
    "US10": "US Americas Inc",
    "DE10": "DE Central Europe GmbH",
    "FR01": "France Operations SAS",
    "UK01": "UK Northern Europe Ltd",
}

FORNECEDORES_FIXOS = [
    ("VEND001", "Tech Solutions LTDA", "12.345.678/0001-91"),
    ("VEND002", "Global Materiais Industriais SA", "23.456.789/0001-82"),
    ("VEND003", "Omega Componentes Eletronicos ME", "34.567.890/0001-73"),
    ("VEND004", "Nord Logistics Brasil LTDA", "45.678.901/0001-64"),
    ("VEND005", "Alpha Quimicos e Solventes SA", "56.789.012/0001-55"),
    ("VEND006", "Delta Maquinas e Ferramentas LTDA", "67.890.123/0001-46"),
    ("VEND007", "Sigma Embalagens Ltda", "78.901.234/0001-37"),
    ("VEND008", "Vertex TI e Servicos SA", "89.012.345/0001-28"),
    ("VEND009", "Prime Energia e Utilidades LTDA", "90.123.456/0001-19"),
    ("VEND010", "Horizon Outsourcing Corporativo ME", "11.223.344/0001-81"),
    ("VEND011", "Catalyst Autopecas Brasil SA", "22.334.455/0001-92"),
    ("VEND012", "Meridian Agronegocios LTDA", "33.445.566/0001-03"),
    ("VEND013", "Apex Materiais de Construcao ME", "44.556.677/0001-14"),
    ("VEND014", "Pioneer Pecas Aeronauticas LTDA", "55.667.788/0001-25"),
    ("VEND015", "Unity Facilities e Manutencao SA", "66.778.899/0001-36"),
    ("VEND016", "Zenith Pharma Insumos LTDA", "77.889.901/0001-47"),
    ("VEND017", "Nova Steel Metalurgica SA", "88.901.233/0001-58"),
    ("VEND018", "Bright Office Supplies ME", "99.011.022/0001-69"),
    ("VEND019", "Atlas Seguranca e EPI LTDA", "10.112.334/0001-70"),
    ("VEND020", "Kappa Servicos Tecnicos SA", "20.223.455/0001-81"),
]


def _mapa_fornecedores() -> dict[str, tuple[str, str]]:
    return {c: (nome, cnpj) for c, nome, cnpj in FORNECEDORES_FIXOS}


def _adicionar_dias(data_iso: str, dias: int) -> str:
    base = np.datetime64(data_iso)
    nova = base + np.timedelta64(dias, "D")
    s = np.datetime_as_string(nova, unit="D")
    return str(s)


def _debit_credito_ap(doc_type: str) -> tuple[str, float]:
    if doc_type in ("KR", "RE"):
        return "H", -1.0
    if doc_type == "KZ":
        return "S", 1.0
    raise ValueError(f"Tipo de documento AP invalido: {doc_type}")


def _gerar_linha_contas_pagar(index: int, rng: np.random.Generator, faker_br: Faker) -> dict[str, object]:
    map_forn = _mapa_fornecedores()

    empresa = str(rng.choice(list(EMPRESAS.keys())))
    supplier_id = str(rng.choice([f[0] for f in FORNECEDORES_FIXOS]))
    vendor_name, cnpj = map_forn[supplier_id]

    doc_type = str(rng.choice(DOC_TYPES_AP))
    debit_credito, fator_valor = _debit_credito_ap(doc_type)

    valor_abs = float(np.round(rng.uniform(500.0, 120_000.0), 2))
    amount_lc = valor_abs * fator_valor

    document_status = str(rng.choice(["Aberto", "Compensado"]))
    ano = int(rng.integers(2023, 2026))
    mes = int(rng.integers(1, 13))
    dia_post = int(rng.integers(1, 29))
    posting_date = f"{ano:04d}-{mes:02d}-{dia_post:02d}"
    dias_doc_offset = int(rng.integers(0, 4))
    document_date = _adicionar_dias(posting_date, -dias_doc_offset) if dias_doc_offset else posting_date

    dias_venc = int(rng.choice([30, 60, 90]))
    due_date = _adicionar_dias(posting_date, dias_venc)

    fiscal_year = int(posting_date[0:4])
    fiscal_period = int(posting_date[5:7])

    if document_status == "Aberto":
        clearing_document = ""
        clearing_date = ""
        valor_aberto = valor_abs
        valor_compensado = 0.0
        dias_para_clear = 0
    else:
        dias_para_clear = int(rng.integers(1, 120))
        clearing_date = _adicionar_dias(posting_date, dias_para_clear)
        clearing_document = str(int(rng.integers(2_000_000_000, 2_999_999_999)))
        valor_aberto = 0.0
        valor_compensado = valor_abs

    texto_map = {"KR": DOCUMENTOS_TEXTO_AP[0], "RE": DOCUMENTOS_TEXTO_AP[1], "KZ": DOCUMENTOS_TEXTO_AP[2]}
    document_text = texto_map[doc_type]

    conta_fornecedor = "210100"

    linha: dict[str, object] = {
        "CompanyCode": empresa,
        "DocumentNumber": str(int(rng.integers(1_000_000_000, 1_999_999_999))),
        "DocumentItem": int(rng.integers(1, 999)),
        "FiscalYear": fiscal_year,
        "Supplier": supplier_id,
        "GLAccount": conta_fornecedor,
        "MandanteCod": "100",
        "Branch": str(rng.choice(["BR01", "SP01", "RJ01", "US10"])),
        "CompanyName": EMPRESAS.get(empresa, empresa),
        "VendorName": vendor_name,
        "DocType": doc_type,
        "PostingDate": posting_date,
        "DocumentDate": document_date,
        "DueDate": due_date,
        "FiscalPeriod": fiscal_period,
        "AmountLocalCurrency": amount_lc,
        "DebitCredit": debit_credito,
        "AmountDocumentCurrency": amount_lc,
        "Currency": str(rng.choice(["BRL", "USD", "EUR"])),
        "PostingKey": str(rng.choice(["21", "25", "31"])),
        "UMSKZ": str(rng.choice(["", "A"])),
        "UMSKS": str(rng.choice(["", "X"])),
        "ZUMSK": str(rng.choice(["", "Z1"])),
        "DocumentText": document_text,
        "ClearingDocument": clearing_document,
        "ClearingDate": clearing_date,
        "CostCenter": faker_br.bothify(text="CC###"),
        "PedidoCompra": faker_br.bothify(text="45########"),
        "GKONT": faker_br.bothify(text="GK######"),
        "GKOAR": str(rng.choice(["K", ""])),
        "CNPJ": cnpj,
        "TipoDespesa": str(rng.choice(["Operacional", "CAPEX", "Servicos Tecnicos"])),
        "DocEstorno": faker_br.bothify(text="REV######"),
        "DocumentStatus": document_status,
        "ValorTotalAberto": valor_aberto,
        "ValorTotalCompensado": valor_compensado,
    }
    return linha


def gerar_contas_pagar(linhas: int = 100_000, semente: int = 42, diretorio_saida: str = "data") -> Path:
    rng = np.random.default_rng(semente)
    faker_br = Faker("pt_BR")
    Faker.seed(semente)

    registros = []
    for index in tqdm(range(linhas), desc="Gerando Contas_Pagar", unit="linhas"):
        registros.append(_gerar_linha_contas_pagar(index, rng, faker_br))

    df = pd.DataFrame(registros, columns=COLUNAS)

    for col_clear in ["ClearingDate", "ClearingDocument"]:
        df[col_clear] = df[col_clear].replace("", pd.NA)

    caminho = Path(diretorio_saida) / "Contas_Pagar.csv"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, index=False, na_rep="")
    return caminho


if __name__ == "__main__":
    print("[ZI_CONTAS_PAGAR] Iniciando geracao do CSV...")
    caminho_csv = gerar_contas_pagar()
    print(f"[ZI_CONTAS_PAGAR] Geracao concluida com sucesso: {caminho_csv.resolve()}")
