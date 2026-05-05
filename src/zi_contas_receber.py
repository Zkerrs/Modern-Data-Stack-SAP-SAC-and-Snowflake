from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker
from tqdm import tqdm

COLUNAS = [
    "CompanyCode", "DocumentNumber", "DocumentItem", "FiscalYear", "Customer", "GLAccount", "MandanteCod",
    "Branch", "CompanyName", "CustomerName", "DocType", "PostingDate", "DocumentDate", "DueDate", "FiscalPeriod",
    "AmountLocalCurrency", "DebitCredit", "AmountDocumentCurrency", "Currency", "PostingKey", "UMSKZ", "UMSKS",
    "ZUMSK", "DocumentText", "ClearingDocument", "ClearingDate", "CostCenter", "ProfitCenter", "PedidoVenda",
    "GKONT", "GKOAR", "CNPJ", "TipoDocumento", "DocEstorno", "DocumentStatus", "ValorTotalAberto",
    "ValorTotalCompensado",
]

DOC_TYPES_AR = ("RV", "DR", "DZ")

DOCUMENTOS_TEXTO_AR = [
    "Faturamento de Venda",
    "Recebimento de Cliente",
    "Nota de Debito",
    "Juros por Atraso",
]

EMPRESAS = {
    "BR01": "Brasil Headquarters SA",
    "US10": "US Americas Inc",
    "DE10": "DE Central Europe GmbH",
    "FR01": "France Operations SAS",
    "UK01": "UK Northern Europe Ltd",
}

CLIENTES_FIXOS = [
    ("CUST001", "TechCorp Brasil", "11.111.111/0001-11"),
    ("CUST002", "Mega Retail Distribuicao SA", "22.222.222/0002-22"),
    ("CUST003", "Omega Industria de Equipamentos LTDA", "33.333.333/0003-33"),
    ("CUST004", "North Trade Importacao ME", "44.444.444/0004-44"),
    ("CUST005", "Solar Energy Projetos SA", "55.555.555/0005-55"),
    ("CUST006", "Delta Pharma Distribuidora LTDA", "66.666.666/0006-66"),
    ("CUST007", "Vertex Construcoes Civis SA", "77.777.777/0007-77"),
    ("CUST008", "Prime Alimentos Atacado ME", "88.888.888/0008-88"),
    ("CUST009", "Horizon Logistica Integrada LTDA", "99.999.999/0009-99"),
    ("CUST010", "Atlas Servicos de TI SA", "12.121.212/0001-21"),
    ("CUST011", "Zenith Moda e Vestuario LTDA", "13.131.313/0001-31"),
    ("CUST012", "Nova Petro Postos e Conveniencia ME", "14.141.414/0001-41"),
    ("CUST013", "Bright Hotelaria e Turismo SA", "15.151.515/0001-51"),
    ("CUST014", "Pioneer Agronegocios LTDA", "16.161.616/0001-61"),
    ("CUST015", "Unity Auto Center ME", "17.171.717/0001-71"),
    ("CUST016", "Kappa Educacao Corporativa SA", "18.181.818/0001-81"),
    ("CUST017", "Meridian Papelaria Corporativa LTDA", "19.191.919/0001-91"),
    ("CUST018", "Apex Telecomunicacoes ME", "21.212.121/0001-12"),
    ("CUST019", "Catalyst Quimica Especializada SA", "31.313.131/0001-13"),
    ("CUST020", "Fusion Hospitalar e Saude LTDA", "41.414.141/0001-14"),
]


def _mapa_clientes() -> dict[str, tuple[str, str]]:
    return {cod: (nome, cnpj) for cod, nome, cnpj in CLIENTES_FIXOS}


def _adicionar_dias(data_iso: str, dias: int) -> str:
    base = np.datetime64(data_iso)
    nova = base + np.timedelta64(dias, "D")
    return str(np.datetime_as_string(nova, unit="D"))


def _debit_credito_ar(doc_type: str) -> tuple[str, float]:
    """RV/DR: conta cliente com debito (S); DZ: credito (H)."""
    if doc_type in ("RV", "DR"):
        return "S", 1.0
    if doc_type == "DZ":
        return "H", -1.0
    raise ValueError(f"Tipo de documento AR invalido: {doc_type}")


def _document_text_ar(doc_type: str, rng: np.random.Generator) -> str:
    if doc_type == "RV":
        return "Faturamento de Venda"
    if doc_type == "DZ":
        return "Recebimento de Cliente"
    if doc_type == "DR":
        return str(rng.choice(["Nota de Debito", "Juros por Atraso"]))
    return str(rng.choice(DOCUMENTOS_TEXTO_AR))


def _gerar_linha_contas_receber(rng: np.random.Generator, faker_br: Faker) -> dict[str, object]:
    map_cli = _mapa_clientes()

    empresa = str(rng.choice(list(EMPRESAS.keys())))
    customer_id = str(rng.choice([c[0] for c in CLIENTES_FIXOS]))
    customer_name, cnpj = map_cli[customer_id]

    doc_type = str(rng.choice(DOC_TYPES_AR))
    debit_credito, fator_valor = _debit_credito_ar(doc_type)

    valor_abs = float(np.round(rng.uniform(500.0, 120_000.0), 2))
    amount_lc = valor_abs * fator_valor

    document_status = str(rng.choice(["Aberto", "Compensado"]))

    ano = int(rng.integers(2023, 2026))
    mes = int(rng.integers(1, 13))
    dia_post = int(rng.integers(1, 29))
    posting_date = f"{ano:04d}-{mes:02d}-{dia_post:02d}"

    dias_doc_offset = int(rng.integers(0, 4))
    document_date = _adicionar_dias(posting_date, -dias_doc_offset) if dias_doc_offset else posting_date

    dias_venc = int(rng.choice([15, 30, 45]))
    due_date = _adicionar_dias(posting_date, dias_venc)

    fiscal_year = int(posting_date[0:4])
    fiscal_period = int(posting_date[5:7])

    if document_status == "Aberto":
        clearing_document = ""
        clearing_date = ""
        valor_aberto = valor_abs
        valor_compensado = 0.0
    else:
        dias_para_clear = int(rng.integers(0, 90))
        clearing_date = _adicionar_dias(posting_date, dias_para_clear)
        clearing_document = str(int(rng.integers(1_400_000_000, 1_499_999_999)))
        valor_aberto = 0.0
        valor_compensado = valor_abs

    document_text = _document_text_ar(doc_type, rng)
    conta_cliente = "120100"

    tipo_doc_label = {"RV": "Fatura Venda", "DR": "Nota Debito Cliente", "DZ": "Recebimento"}[doc_type]

    return {
        "CompanyCode": empresa,
        "DocumentNumber": str(int(rng.integers(1_000_000_000, 1_999_999_999))),
        "DocumentItem": int(rng.integers(1, 999)),
        "FiscalYear": fiscal_year,
        "Customer": customer_id,
        "GLAccount": conta_cliente,
        "MandanteCod": "100",
        "Branch": str(rng.choice(["BR01", "SP01", "RJ01", "US10"])),
        "CompanyName": EMPRESAS.get(empresa, empresa),
        "CustomerName": customer_name,
        "DocType": doc_type,
        "PostingDate": posting_date,
        "DocumentDate": document_date,
        "DueDate": due_date,
        "FiscalPeriod": fiscal_period,
        "AmountLocalCurrency": amount_lc,
        "DebitCredit": debit_credito,
        "AmountDocumentCurrency": amount_lc,
        "Currency": str(rng.choice(["BRL", "USD", "EUR", "GBP"])),
        "PostingKey": str(rng.choice(["01", "11", "15"])),
        "UMSKZ": str(rng.choice(["", "A"])),
        "UMSKS": str(rng.choice(["", "X"])),
        "ZUMSK": str(rng.choice(["", "Z1"])),
        "DocumentText": document_text,
        "ClearingDocument": clearing_document,
        "ClearingDate": clearing_date,
        "CostCenter": faker_br.bothify(text="CC###"),
        "ProfitCenter": faker_br.bothify(text="PC###"),
        "PedidoVenda": faker_br.bothify(text="SO########"),
        "GKONT": faker_br.bothify(text="GK######"),
        "GKOAR": str(rng.choice(["D", ""])),
        "CNPJ": cnpj,
        "TipoDocumento": tipo_doc_label,
        "DocEstorno": faker_br.bothify(text="STO######"),
        "DocumentStatus": document_status,
        "ValorTotalAberto": valor_aberto,
        "ValorTotalCompensado": valor_compensado,
    }


def gerar_contas_receber(linhas: int = 100_000, semente: int = 42, diretorio_saida: str = "data") -> Path:
    rng = np.random.default_rng(semente)
    faker_br = Faker("pt_BR")
    Faker.seed(semente)

    registros: list[dict[str, object]] = []
    for _ in tqdm(range(linhas), desc="Gerando Contas_Receber", unit="linhas"):
        registros.append(_gerar_linha_contas_receber(rng, faker_br))

    df = pd.DataFrame(registros, columns=COLUNAS)

    for col_clear in ("ClearingDate", "ClearingDocument"):
        df[col_clear] = df[col_clear].replace("", pd.NA)

    caminho = Path(diretorio_saida) / "Contas_Receber.csv"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, index=False, na_rep="")
    return caminho


if __name__ == "__main__":
    print("[ZI_CONTAS_RECEBER] Iniciando geracao do CSV...")
    caminho_csv = gerar_contas_receber()
    print(f"[ZI_CONTAS_RECEBER] Geracao concluida com sucesso: {caminho_csv.resolve()}")
