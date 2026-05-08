"""
Dimensoes sinteticas CANONICAS para CSVs tipo CDS SAP (S/4HANA).

Os CSVs das views **standard** `I_Customer`, `I_Supplier` etc. **nao** devem ter
colunas alem do CDS (sem `CompanyCode` no cliente/fornecedor central se o SAP nao
expor esse elemento na mesma view).

Para **fatos** (`ZI_*`, GL, estoque) e dimensoes como `I_CompanyCode`, usar estes
mestres (`CompanyCode`, `Plant`, `GLAccount`, grupos, mandante, seed, faixas KUNNR/LIFNR`)
para manter consistencia entre extracoes.

Aumentar dimensoes: edite este modulo (ou acrescente entradas), nao invente
codigos paralelos dentro de cada script isolado.
"""

from __future__ import annotations

# Seed padrao de todo dado sintetico dimension/fato deste repo.
SYNTHETIC_MASTER_SEED = 20260506

# KUNNR / LIFNR — numero inicial ao gerar sequencias com zero a esquerda (10 chars).
DEFAULT_START_CUSTOMER_NUMBER = 10_000_101
DEFAULT_START_SUPPLIER_NUMBER = 20_000_001

MASTER_CLIENT_IDS: tuple[str, ...] = (
    "100",
    "200",
    "300",
    "400",
    "510",
    "600",
    "700",
    "812",
)

# Alinhado as definicoes ZI_* em CDS/ e a fatos analiticos futuros neste repo.
MASTER_COMPANY_CODES: tuple[dict[str, str], ...] = (
    {"CompanyCode": "BR01", "CompanyCodeCurrency": "BRL", "CompanyName": "Brasil Operacoes"},
    {"CompanyCode": "US10", "CompanyCodeCurrency": "USD", "CompanyName": "US Operations Inc."},
    {"CompanyCode": "DE10", "CompanyCodeCurrency": "EUR", "CompanyName": "DE Zentrale AG"},
    {"CompanyCode": "FR01", "CompanyCodeCurrency": "EUR", "CompanyName": "FR Holdings SAS"},
    {"CompanyCode": "UK01", "CompanyCodeCurrency": "GBP", "CompanyName": "UK Trading Ltd"},
)

MASTER_PLANTS: tuple[str, ...] = ("P001", "P002", "P003", "P004")

MASTER_PLANT_NAMES: dict[str, str] = {
    "P001": "Fabrica Matriz SP",
    "P002": "Centro Distribuicao RJ",
    "P003": "Planta Exportacao SC",
    "P004": "Filial Norte",
}

MASTER_PROFIT_CENTERS: tuple[str, ...] = ("PC-1000", "PC-2000", "PC-3000")

# Contas usadas em custo / estoque de exemplo; expanda conforme CDS reais.
MASTER_GL_ACCOUNTS: tuple[dict[str, str], ...] = (
    {"GLAccount": "130100", "GLAccountName": "Estoque Prod. Acabado"},
    {"GLAccount": "130200", "GLAccountName": "Estoque Matéria Prima"},
    {"GLAccount": "130300", "GLAccountName": "Estoque Merc. Revenda"},
    {"GLAccount": "003110100", "GLAccountName": "Faturamento bruto (ex. 31101)"},
    {"GLAccount": "003120100", "GLAccountName": "Faturamento bruto (ex. 31201)"},
    {"GLAccount": "003110200", "GLAccountName": "Deducoes / impostos (ex. 31102)"},
)

MASTER_CUSTOMER_ACCOUNT_GROUPS: tuple[str, ...] = (
    "ZAG1",
    "ZAG2",
    "ZCUS",
    "ZOTH",
    "ZPHM",
    "ZREV",
    "ZDTR",
    "ZEXP",
    "ZINT",
    "ZGOV",
)

# Grupos de conta fornecedor (KTOKK) — mesma filosofia dos grupos de cliente.
MASTER_SUPPLIER_ACCOUNT_GROUPS: tuple[str, ...] = (
    "ZE01",
    "ZE02",
    "ZLIF",
    "ZIMP",
    "ZSVC",
    "ZOTH",
)


def supplier_account_groups_list() -> list[str]:
    return list(MASTER_SUPPLIER_ACCOUNT_GROUPS)


def company_codes_list() -> list[str]:
    return [x["CompanyCode"] for x in MASTER_COMPANY_CODES]


def gl_accounts_list() -> list[str]:
    return [x["GLAccount"] for x in MASTER_GL_ACCOUNTS]


def pad_kunnr_lifnr(num: int) -> str:
    return str(num).zfill(10)[:10]


# Empresa deterministica por pais para fatos/CDS que tenham CompanyCode mas nao BU na dimensao.
_COUNTRY_PRIMARY_COMPANY: dict[str, str] = {
    "BR": "BR01",
    "US": "US10",
    "DE": "DE10",
    "FR": "FR01",
    "GB": "UK01",
    "UK": "UK01",
    "MX": "US10",
    "CA": "US10",
    "IT": "DE10",
    "ES": "FR01",
    "JP": "US10",
    "PT": "FR01",
}


def company_code_for_country(country: str) -> str:
    cc = (country or "").strip().upper()
    return _COUNTRY_PRIMARY_COMPANY.get(cc, MASTER_COMPANY_CODES[0]["CompanyCode"])


# --- CSV I_Customer: volume alvo (CI) e saida enxuta -----------------

I_CUSTOMER_MIN_ROWS = 120_000
I_CUSTOMER_DEFAULT_ROWS = 120_000
I_CUSTOMER_MAX_ROWS = 150_000
# Smokes / testes locais (fora da faixa 120k–150k)
I_CUSTOMER_QUICK_TEST_ROWS = 600

# I_CostCenter (dimensao CO) — mesmo volume-alvo que I_Customer / I_GLAccount.
I_COSTCENTER_MIN_ROWS = 120_000
I_COSTCENTER_DEFAULT_ROWS = 120_000
I_COSTCENTER_MAX_ROWS = 150_000
I_COSTCENTER_QUICK_TEST_ROWS = 600

# I_ProfitCenter — mesmo volume-alvo que I_Customer / I_GLAccount / I_CostCenter.
I_PROFITCENTER_MIN_ROWS = 120_000
I_PROFITCENTER_DEFAULT_ROWS = 120_000
I_PROFITCENTER_MAX_ROWS = 150_000
I_PROFITCENTER_QUICK_TEST_ROWS = 600

# I_Product (material master) — volume tipicamente menor que dimensoes transacionais (cliente, GL, CO).
I_PRODUCT_MIN_ROWS = 5_000
I_PRODUCT_DEFAULT_ROWS = 28_000
I_PRODUCT_MAX_ROWS = 65_000
I_PRODUCT_QUICK_TEST_ROWS = 400

# I_ProductType — seguindo padrao high-cardinal do projeto (120k–150k fora de --quick).
I_PRODUCTTYPE_MIN_ROWS = 120_000
I_PRODUCTTYPE_DEFAULT_ROWS = 120_000
I_PRODUCTTYPE_MAX_ROWS = 150_000
I_PRODUCTTYPE_QUICK_TEST_ROWS = 600

MASTER_PRODUCT_TYPES: tuple[str, ...] = ("FERT", "HALB", "ROH", "HAWA", "NLAG", "DIEN", "ERSA")
MASTER_PRODUCT_GROUPS: tuple[str, ...] = ("Z001", "Z002", "Z010", "Z020", "Z030", "ZMAT", "ZSRV")

# Areas de contabilidade de custos (KOKRS) — rotacionar com CompanyCode nos geradores.
MASTER_CONTROLLING_AREAS: tuple[str, ...] = ("0001", "A000", "CORP", "O100")


def csv_cell_has_semantic_value(value: object) -> bool:
    """True se a celula nao e 'sem dado' (null, string vazia ou so espacos)."""
    if value is None:
        return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return True
    s = str(value).strip()
    return bool(s)


def column_order_excluding_always_empty(
    column_order: list[str],
    rows: list[dict[str, str]],
) -> list[str]:
    """
    Mantem a ordem original; remove colunas em que TODAS as linhas estao vazias.
    Se nao houver linhas, devolve a ordem completa (nao ha evidencia para cortar).
    """
    if not rows:
        return list(column_order)
    return [
        c
        for c in column_order
        if any(csv_cell_has_semantic_value(r.get(c)) for r in rows)
    ]
