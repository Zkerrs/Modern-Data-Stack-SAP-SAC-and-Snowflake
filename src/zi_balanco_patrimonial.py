from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm
from faker import Faker


COLUNAS = [
    "CompanyCode", "Ledger", "DocumentNumber", "DocumentItem", "FiscalYear", "FiscalPeriod",
    "PostingDate", "DocumentDate", "ClearingDate", "ChartOfAccounts", "GLAccount",
    "GLAccountName", "GLAccountType", "GLAccountTypeName", "GLAccountGroup",
    "GLAccountGroupName", "ProfitCenter", "ProfitCenterName", "CostCenter",
    "CostCenterName", "Branch", "Segment", "FunctionalArea", "Plant", "PlantName",
    "DocType", "NotaFiscal_XBLNR", "Atribuicao_ZUONR", "DocumentText",
    "DebitCreditCode", "Currency", "AmountInCompanyCurrency",
]

DOMINIOS = {
    "Ledger": ["0L", "2L", "3L"],
    "CompanyCode": ["BR01", "US10", "DE10", "FR01", "UK01"],
    "ChartOfAccounts": ["YCOA", "CBR1", "CUS1"],
    "Currency": ["BRL", "USD", "EUR", "GBP"],
    "DebitCreditCode": ["S", "H"],
    "DocType": ["SA", "KR", "KZ", "DZ", "DR", "RV", "WE", "RE"],
    "Segment": ["SEGM_A", "SEGM_B", "SEGM_C"],
    "Plant": ["P001", "P002", "P003", "P004"],
    "CostCenterName": ["Recursos Humanos", "TI Global", "Vendas Corporativas", "Producao Linha 1"],
    "DocumentText": [
        "Aquisicao de Imobilizado",
        "Recebimento de Cliente",
        "Pagamento de Fornecedor",
        "Ajuste de Estoque",
        "Aporte de Capital",
        "Provisionamento de Impostos",
    ],
}

CONTAS_BP = {
    "100100": {"nome": "Caixa e Equivalentes", "tipo": "AST", "grupo": "Ativo Circulante", "natureza": "ATIVO"},
    "120100": {"nome": "Contas a Receber de Clientes", "tipo": "AST", "grupo": "Ativo Circulante", "natureza": "ATIVO"},
    "130100": {"nome": "Estoque de Produtos Acabados", "tipo": "AST", "grupo": "Ativo Circulante", "natureza": "ATIVO"},
    "130200": {"nome": "Estoque de Materiais (ROH)", "tipo": "AST", "grupo": "Ativo Circulante", "natureza": "ATIVO"},
    "160100": {"nome": "Maquinas e Equipamentos (Imobilizado)", "tipo": "AST", "grupo": "Ativo Nao Circulante", "natureza": "ATIVO"},
    "160199": {"nome": "Depreciacao Acumulada", "tipo": "AST", "grupo": "Ativo Nao Circulante", "natureza": "ATIVO_REDUTORA"},
    "210100": {"nome": "Contas a Pagar Fornecedores", "tipo": "LIA", "grupo": "Passivo Circulante", "natureza": "PASSIVO_PL"},
    "220100": {"nome": "Impostos a Recolher", "tipo": "LIA", "grupo": "Passivo Circulante", "natureza": "PASSIVO_PL"},
    "230100": {"nome": "Emprestimos de Curto Prazo", "tipo": "LIA", "grupo": "Passivo Circulante", "natureza": "PASSIVO_PL"},
    "290100": {"nome": "Capital Social", "tipo": "LIA", "grupo": "Patrimonio Liquido", "natureza": "PASSIVO_PL"},
    "290200": {"nome": "Lucros Acumulados", "tipo": "LIA", "grupo": "Patrimonio Liquido", "natureza": "PASSIVO_PL"},
}


def _sortear_debito_credito(natureza: str, rng: np.random.Generator) -> str:
    # Regra FI: ativos majoritariamente em debito, passivo/pl majoritariamente em credito.
    if natureza == "ATIVO":
        return str(rng.choice(["S", "H"], p=[0.70, 0.30]))
    if natureza == "ATIVO_REDUTORA":
        return str(rng.choice(["S", "H"], p=[0.30, 0.70]))
    return str(rng.choice(["S", "H"], p=[0.30, 0.70]))


def _gerar_linha_coerente(i: int, rng: np.random.Generator, faker_br: Faker) -> dict[str, object]:
    gl_account = str(rng.choice(list(CONTAS_BP.keys())))
    conta = CONTAS_BP[gl_account]
    dc = _sortear_debito_credito(conta["natureza"], rng)

    ano = int(rng.integers(2023, 2026))
    periodo = int(rng.integers(1, 13))
    dia_post = int(rng.integers(1, 29))
    dia_doc = int(rng.integers(1, 29))
    dia_clear = int(rng.integers(1, 29))

    valor_base = float(np.round(rng.uniform(500, 250000), 2))
    # Regra solicitada: S positivo, H negativo
    amount = valor_base if dc == "S" else -valor_base

    linha: dict[str, object] = {
        "CompanyCode": str(rng.choice(DOMINIOS["CompanyCode"])),
        "Ledger": str(rng.choice(DOMINIOS["Ledger"])),
        "DocumentNumber": str(int(rng.integers(1000000000, 1999999999))),
        "DocumentItem": int(rng.integers(1, 10)),
        "FiscalYear": ano,
        "FiscalPeriod": periodo,
        "PostingDate": f"{ano:04d}-{periodo:02d}-{dia_post:02d}",
        "DocumentDate": f"{ano:04d}-{periodo:02d}-{dia_doc:02d}",
        "ClearingDate": f"{ano:04d}-{periodo:02d}-{dia_clear:02d}",
        "ChartOfAccounts": str(rng.choice(DOMINIOS["ChartOfAccounts"])),
        "GLAccount": gl_account,
        # Vínculo estrito exigido
        "GLAccountName": conta["nome"],
        "GLAccountType": conta["tipo"],
        "GLAccountTypeName": "Balance Sheet Account",
        "GLAccountGroup": conta["grupo"].replace(" ", "_").upper(),
        "GLAccountGroupName": conta["grupo"],
        "ProfitCenter": faker_br.bothify(text="PC###"),
        "ProfitCenterName": faker_br.company(),
        "CostCenter": faker_br.bothify(text="CC###"),
        "CostCenterName": str(rng.choice(DOMINIOS["CostCenterName"])),
        "Branch": faker_br.bothify(text="BR##"),
        "Segment": str(rng.choice(DOMINIOS["Segment"])),
        "FunctionalArea": faker_br.bothify(text="FA###"),
        "Plant": str(rng.choice(DOMINIOS["Plant"])),
        "PlantName": faker_br.company(),
        "DocType": str(rng.choice(DOMINIOS["DocType"])),
        "NotaFiscal_XBLNR": faker_br.bothify(text="NF########"),
        "Atribuicao_ZUONR": faker_br.bothify(text="ATR######"),
        "DocumentText": str(rng.choice(DOMINIOS["DocumentText"])),
        "DebitCreditCode": dc,
        "Currency": str(rng.choice(DOMINIOS["Currency"])),
        "AmountInCompanyCurrency": amount,
    }
    return linha


def gerar_balanco_patrimonial(linhas: int = 120000, semente: int = 42, diretorio_saida: str = "data") -> Path:
    rng = np.random.default_rng(semente)
    faker_br = Faker("pt_BR")
    Faker.seed(semente)
    registros = []
    for i in tqdm(range(linhas), desc="Gerando Balanco_Patrimonial", unit="linhas"):
        linha = _gerar_linha_coerente(i, rng, faker_br)
        registros.append(linha)
    df = pd.DataFrame(registros)
    caminho = Path(diretorio_saida) / "Balanco_Patrimonial.csv"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, index=False)
    return caminho


if __name__ == "__main__":
    print("[ZI_BALANCO_PATRIMONIAL] Iniciando geracao do CSV...")
    saida = gerar_balanco_patrimonial()
    print(f"[ZI_BALANCO_PATRIMONIAL] Geracao concluida com sucesso: {saida.resolve()}")
