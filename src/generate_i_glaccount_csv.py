"""
Gera I_GLAccount.csv com Plano de Contas SAP hierarquico (multiplos niveis).

Layout exportado:
  ChartOfAccounts, GLAccount, GLAccountName, GLAccountGroup,
  GLAccountType, IsBalanceSheetAccount, ParentAccount
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

GLACCOUNT_COLUMNS = [
    "ChartOfAccounts",
    "GLAccount",
    "GLAccountName",
    "GLAccountGroup",
    "GLAccountType",
    "IsBalanceSheetAccount",
    "ParentAccount",
]

CHART_OF_ACCOUNTS = "YCOA"

def _node(gl: str, name: str, group: str, gl_type: str, parent: str) -> dict[str, str]:
    return {
        "GLAccount": gl,
        "GLAccountName": name,
        "GLAccountGroup": group,
        "GLAccountType": gl_type,
        "IsBalanceSheetAccount": "X" if (gl in {"BP", "1", "2", "3"} or (gl[:1] in {"1", "2", "3"} and len(gl) == 6)) else "",
        "ParentAccount": parent,
    }


def _leaf(gl: str, name: str, group: str, gl_type: str, parent: str) -> dict[str, str]:
    return {
        "GLAccount": gl,
        "GLAccountName": name,
        "GLAccountGroup": group,
        "GLAccountType": gl_type,
        "IsBalanceSheetAccount": "X" if gl[:1] in {"1", "2", "3"} else "",
        "ParentAccount": parent,
    }


def _auto_posting_nodes(
    root3: str,
    branches: tuple[tuple[str, str, str, tuple[str, ...]], ...],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Gera nivel 4 (ABBx10) e folhas numeradas sob cada ABC000 sintetico."""
    parent = f"{int(root3):03d}000"
    nodes_o: list[dict[str, str]] = []
    leaf_o: list[dict[str, str]] = []
    for idx, (sub_name, grp, glt, lnames) in enumerate(branches, start=1):
        mid_num = int(root3) * 1000 + 100 + 10 * idx
        mid_gl = f"{mid_num:06d}"
        nodes_o.append(_node(mid_gl, sub_name, grp, glt, parent))
        if len(lnames) > 9:
            raise ValueError(f"Demasiadas folhas sob {mid_gl} (max 9)")
        for j, ln in enumerate(lnames, start=1):
            leaf_gl = f"{mid_num + j:06d}"
            leaf_o.append(_leaf(leaf_gl, ln, grp, glt, mid_gl))
    return nodes_o, leaf_o


def _mega(
    root3: int,
    sections: tuple[tuple[str, str, str, str], ...],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Atalho: quarteto (titulo, grupo, tipo GL, nomes folha separados por ';')."""
    tup = tuple(
        (tit, grp, glt, tuple(s.strip() for s in ln.split(";") if s.strip()))
        for tit, grp, glt, ln in sections
    )
    return _auto_posting_nodes(f"{root3:03d}", tup)


BASE_NODES: list[dict[str, str]] = [
    _node("ALL", "Plano de Contas Corporativo", "ROOT", "N", ""),
    _node("BP", "Balanco Patrimonial", "BAL", "X", "ALL"),
    _node("DRE", "Demonstracao do Resultado", "ROOT", "N", "ALL"),
    _node("1", "Ativo", "BAL", "X", "BP"),
    _node("2", "Passivo", "BAL", "X", "BP"),
    _node("3", "Patrimonio Liquido", "BAL", "X", "BP"),
    _node("4", "Receitas", "REV", "P", "DRE"),
    _node("5", "Custos", "EXP", "P", "DRE"),
    _node("6", "Despesas Operacionais", "EXP", "P", "DRE"),
]

# Nivel 3 (contas sinteticas tipo nos SAP)
LEVEL3_NODES: list[dict[str, str]] = [
    _node("110000", "Disponibilidades", "BAL", "X", "1"),
    _node("115000", "Aplicacoes e Titulos Liquidez Imediata", "BAL", "X", "1"),
    _node("118000", "Outras Disponibilidades", "BAL", "X", "1"),
    _node("120000", "Contas a Receber", "BAL", "X", "1"),
    _node("125000", "Cartoes Credito Debito POS", "BAL", "X", "1"),
    _node("130000", "Estoques", "MAT", "X", "1"),
    _node("135000", "Estoques em Transito Third Party", "MAT", "X", "1"),
    _node("140000", "Tributos a Recuperar", "BAL", "X", "1"),
    _node("145000", "Tributos Diferidos Ativo Circulante", "BAL", "X", "1"),
    _node("150000", "Adiantamentos e Outros Direitos Circulantes", "BAL", "X", "1"),
    _node("155000", "Credito Judicial e Fiscal Diferido", "BAL", "X", "1"),
    _node("160000", "Imobilizado", "BAL", "X", "1"),
    _node("165000", "Imobilizado em Andamento CPC", "BAL", "X", "1"),
    _node("170000", "Intangivel", "BAL", "X", "1"),
    _node("175000", "Investimento MEP Equivalente Patrimonio", "BAL", "X", "1"),
    _node("180000", "Outros Ativos Nao Circulantes", "BAL", "X", "1"),
    _node("210000", "Fornecedores a Pagar", "BAL", "X", "2"),
    _node("215000", "Obrigacoes Fiscais Diferidas LP", "BAL", "X", "2"),
    _node("220000", "Obrigações Trabalhistas", "BAL", "X", "2"),
    _node("225000", "Participacoes e Lucros a Distribuir", "BAL", "X", "2"),
    _node("230000", "Emprestimos e Financiamentos", "BAL", "X", "2"),
    _node("235000", "Debentures e Titulos Emitidos", "BAL", "X", "2"),
    _node("240000", "Tributos a Recolher", "BAL", "X", "2"),
    _node("245000", "Obrigacoes Trabalhistas Fiscais Diversos", "BAL", "X", "2"),
    _node("250000", "Receitas Diferidas LP", "BAL", "X", "2"),
    _node("260000", "Provisões Judiciais e Trabalhistas", "BAL", "X", "2"),
    _node("270000", "Passivo Fiscal Diferido", "BAL", "X", "2"),
    _node("275000", "Outros Passivos Nao Circulantes", "BAL", "X", "2"),
    _node("280000", "Intercompany Consolidacao CPC", "BAL", "X", "2"),
    _node("310000", "Capital e Reservas", "BAL", "X", "3"),
    _node("315000", "Ajustes Avaliacao Patrimonial", "BAL", "X", "3"),
    _node("320000", "Lucros Prejuizos Retidos Movimento", "BAL", "X", "3"),
    _node("325000", "Dividendos JCP Provisionados PL", "BAL", "X", "3"),
    _node("410000", "Receita de Vendas", "REV", "P", "4"),
    _node("415000", "Receita Prestacao Bundled Services", "REV", "P", "4"),
    _node("420000", "Receita de Servicos", "REV", "P", "4"),
    _node("425000", "Receita SaaS Contratos Multi Ano", "REV", "P", "4"),
    _node("430000", "Receitas Financeiras", "REV", "N", "4"),
    _node("435000", "Resultado Equivalence Patrimonial", "REV", "N", "4"),
    _node("438000", "Outras Operacionais Credoras", "REV", "P", "4"),
    _node("440000", "Deduções e Devolucões sobre Receitas", "REV", "P", "4"),
    _node("450000", "Subvencoes e Incentivos Reconhecidos", "REV", "N", "4"),
    _node("510000", "Custo dos Produtos Vendidos", "EXP", "P", "5"),
    _node("515000", "Custo Indiretos Producao Alocados", "EXP", "P", "5"),
    _node("520000", "Custo de Servicos Prestados", "EXP", "P", "5"),
    _node("522000", "Custo Horas Tecnicas Outsourcing CO", "EXP", "P", "5"),
    _node("530000", "Custos Logísticos", "EXP", "P", "5"),
    _node("535000", "Garantias Tecnicas Warranty COGS", "EXP", "P", "5"),
    _node("540000", "Tributos Incidentes sobre Vendas", "EXP", "P", "5"),
    _node("550000", "Ajustes Inventario Baixa Impairment", "EXP", "P", "5"),
    _node("560000", "Seguros Produção Fabrica CO", "EXP", "P", "5"),
    _node("610000", "Despesas com Pessoal", "EXP", "P", "6"),
    _node("612000", "Beneficios Vale Refeicao Transporte", "EXP", "P", "6"),
    _node("615000", "Treinamento RH Desenvolvimento", "EXP", "P", "6"),
    _node("617000", "Plano Saude Assistencia Medica", "EXP", "P", "6"),
    _node("618000", "Previdência Complementar Boni", "EXP", "P", "6"),
    _node("620000", "Despesas Administrativas", "EXP", "P", "6"),
    _node("622000", "Seguros Corporativos Diversos", "EXP", "P", "6"),
    _node("624000", "Despesas com Viagens Corporativas Gerais", "EXP", "P", "6"),
    _node("625000", "Material Escritório Correspondências", "EXP", "P", "6"),
    _node("626000", "Manut Predial Facilities", "EXP", "P", "6"),
    _node("630000", "Despesas de TI", "EXP", "P", "6"),
    _node("632000", "Ciberseguranca e Observabilidade SaaS", "EXP", "P", "6"),
    _node("634000", "Data e Analytics Plataforma", "EXP", "P", "6"),
    _node("640000", "Despesas de Marketing", "EXP", "P", "6"),
    _node("642000", "Marketing Performance Partners", "EXP", "P", "6"),
    _node("645000", "Branding Sponsorship", "EXP", "P", "6"),
    _node("650000", "Despesas Comerciais", "EXP", "P", "6"),
    _node("652000", "POS Merchandising Trade Marketing", "EXP", "P", "6"),
    _node("655000", "Research Cliente VOC Programas", "EXP", "P", "6"),
    _node("660000", "Despesas Gerais com Terceiros", "EXP", "P", "6"),
    _node("662000", "Servicos Outsourcing SSC Financeiro RH", "EXP", "P", "6"),
    _node("665000", "Tax Consulting Transfer Pricing", "EXP", "P", "6"),
    _node("668000", "Seguros Credito Titulos Avalistas", "EXP", "P", "6"),
    _node("670000", "Depreciação Amortização Exaustão", "EXP", "P", "6"),
    _node("675000", "Arrendamentos IFRS CPC IFRS16", "EXP", "P", "6"),
    _node("680000", "Despesas Financeiras", "EXP", "N", "6"),
    _node("685000", "Resultado Monetario Fiscal Inflação", "EXP", "N", "6"),
    _node("690000", "Tributos Lucro LP IRPJ CSLL", "EXP", "N", "6"),
    _node("692000", "Contrib Social Lucro Liquido Parcelamentos", "EXP", "N", "6"),
    _node("695000", "Outras Receitas Despesas Nao Operacionais", "EXP", "N", "6"),
]

def _rollup_specs_from_sidecar() -> tuple[str, ...]:
    path = Path(__file__).resolve().with_name("_i_glaccount_rollups.txt")
    if not path.is_file():
        raise FileNotFoundError(f"Tabela rollup em falta: {path}")
    raw = path.read_text(encoding="utf-8")
    return tuple(ln.strip() for ln in raw.splitlines() if ln.strip() and not ln.startswith("#"))


def _gather_rollups_from_rows(rows: tuple[str, ...]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    buckets: defaultdict[int, list[tuple[str, str, str, tuple[str, ...]]]] = defaultdict(list)
    for ln in rows:
        parts = ln.split("|", maxsplit=4)
        if len(parts) != 5:
            raise ValueError(f"Linha rollup invalida ({len(parts)} campos): {ln!r}")
        root_s, subtitle, grp, glt, pack = parts
        leafs = tuple(s.strip() for s in pack.split(";") if s.strip())
        if not leafs:
            raise ValueError(f"Linha rollup sem folhas: {ln!r}")
        buckets[int(root_s)].append((subtitle.strip(), grp.strip(), glt.strip(), leafs))
    l4_roll: list[dict[str, str]] = []
    fin_roll: list[dict[str, str]] = []
    for root in sorted(buckets):
        lx4, lxfin = _auto_posting_nodes(f"{root:03d}", tuple(buckets[root]))
        l4_roll.extend(lx4)
        fin_roll.extend(lxfin)
    return l4_roll, fin_roll


def _assemble_detail_accounts() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    l4_core: list[dict[str, str]] = [
        _node("110100", "Caixa e Numerarios", "BAL", "X", "110000"),
        _node("110200", "Bancos", "BAL", "X", "110000"),
        _node("110300", "Aplicações Financeiras", "BAL", "X", "110000"),
        _node("120100", "Clientes Nacionais", "BAL", "X", "120000"),
        _node("120200", "Clientes Estrangeiros", "BAL", "X", "120000"),
        _node("120300", "Intercompany a Receber", "BAL", "X", "120000"),
        _node("130100", "Estoque de Matéria Prima", "MAT", "X", "130000"),
        _node("130200", "Estoque de Produto Acabado", "MAT", "X", "130000"),
        _node("130300", "Estoque de Mercadoria Revenda", "MAT", "X", "130000"),
        _node("160100", "Terrenos e Edificios", "BAL", "X", "160000"),
        _node("160200", "Maquinas e Equipamentos", "BAL", "X", "160000"),
        _node("160300", "Veiculos", "BAL", "X", "160000"),
        _node("210100", "Fornecedores Nacionais", "BAL", "X", "210000"),
        _node("210200", "Fornecedores Estrangeiros", "BAL", "X", "210000"),
        _node("210300", "Fornecedores Intercompany", "BAL", "X", "210000"),
        _node("220100", "Salarios a Pagar", "BAL", "X", "220000"),
        _node("220200", "Encargos e Beneficios", "BAL", "X", "220000"),
        _node("410100", "Receita de Produtos", "REV", "P", "410000"),
        _node("410200", "Receita de Software", "REV", "P", "410000"),
        _node("410300", "Receita de Hardware", "REV", "P", "410000"),
        _node("420100", "Receita de Consultoria", "REV", "P", "420000"),
        _node("420200", "Receita de Suporte", "REV", "P", "420000"),
        _node("510100", "CPV Material Direto", "MAT", "P", "510000"),
        _node("510200", "CPV Mao de Obra Direta", "EXP", "P", "510000"),
        _node("610100", "Salarios e Prolabore", "EXP", "P", "610000"),
        _node("610200", "Ferias e 13 Salario", "EXP", "P", "610000"),
        _node("630100", "Infraestrutura TI", "EXP", "P", "630000"),
        _node("630200", "Softwares e Licenças", "EXP", "P", "630000"),
        _node("640100", "Publicidade e Midia", "EXP", "P", "640000"),
        _node("640200", "Eventos e Campanhas", "EXP", "P", "640000"),
    ]

    fin_core: list[dict[str, str]] = [
    _leaf("110101", "Caixa Matriz", "BAL", "X", "110100"),
    _leaf("110102", "Caixa Filial", "BAL", "X", "110100"),
    _leaf("110201", "Banco do Brasil Conta Corrente", "BAL", "X", "110200"),
    _leaf("110202", "Itau Conta Corrente", "BAL", "X", "110200"),
    _leaf("110203", "Santander Conta Corrente", "BAL", "X", "110200"),
    _leaf("110204", "Bradesco PJ Conta Operacional", "BAL", "X", "110200"),
    _leaf("110205", "C6 Bank Liquidez D0", "BAL", "X", "110200"),
    _leaf("110206", "Exterior JP Morgan Cash US", "BAL", "X", "110200"),
    _leaf("110103", "Caixa PDV Marketplace", "BAL", "X", "110100"),
    _leaf("110104", "Numerario Custodia Overnight", "BAL", "X", "110100"),
    _leaf("110301", "Aplicacao CDB Curto Prazo", "BAL", "X", "110300"),
    _leaf("110302", "Aplicacao Fundo DI", "BAL", "X", "110300"),
    _leaf("110303", "CRI CRA Liquida D1 Custodia", "BAL", "X", "110300"),
    _leaf("120101", "Clientes Varejo Nacional", "BAL", "X", "120100"),
    _leaf("120102", "Clientes Atacado Nacional", "BAL", "X", "120100"),
    _leaf("120103", "Clientes Governo e Eletivas", "BAL", "X", "120100"),
    _leaf("120104", "Clientes Ecommerce Omnichannel", "BAL", "X", "120100"),
    _leaf("120201", "Clientes Americas", "BAL", "X", "120200"),
    _leaf("120202", "Clientes Europa", "BAL", "X", "120200"),
    _leaf("120301", "Intercompany BR01", "BAL", "X", "120300"),
    _leaf("120302", "Intercompany US10", "BAL", "X", "120300"),
    _leaf("130101", "Aco e Ligas Metálicas", "MAT", "X", "130100"),
    _leaf("130102", "Resinas e Polimeros", "MAT", "X", "130100"),
    _leaf("130201", "Produtos Acabados Linha A", "MAT", "X", "130200"),
    _leaf("130202", "Produtos Acabados Linha B", "MAT", "X", "130200"),
    _leaf("130301", "Mercadorias Revenda Nacional", "MAT", "X", "130300"),
    _leaf("130302", "Mercadorias Revenda Importada", "MAT", "X", "130300"),
    _leaf("140101", "ICMS a Recuperar", "BAL", "X", "140000"),
    _leaf("140102", "PIS COFINS a Recuperar", "BAL", "X", "140000"),
    _leaf("160101", "Terrenos Industriais", "BAL", "X", "160100"),
    _leaf("160102", "Edificios Administrativos", "BAL", "X", "160100"),
    _leaf("160201", "Servidores e Storage", "BAL", "X", "160200"),
    _leaf("160202", "Máquinas Produção", "BAL", "X", "160200"),
    _leaf("160301", "Frota Comercial", "BAL", "X", "160300"),
    _leaf("160302", "Frota Logistica", "BAL", "X", "160300"),
    _leaf("170101", "Software ERP", "BAL", "X", "170000"),
    _leaf("170102", "Licenças Industriais", "BAL", "X", "170000"),
    _leaf("170103", "Goodwill Consolidacao CPC", "BAL", "X", "170000"),
    _leaf("170104", "Software Capitalizado Agil Cust Dev", "BAL", "X", "170000"),
    _leaf("210101", "Fornecedores Nacionais MP", "BAL", "X", "210100"),
    _leaf("210102", "Fornecedores Nacionais Serviços", "BAL", "X", "210100"),
    _leaf("210201", "Fornecedores Estrangeiros USD", "BAL", "X", "210200"),
    _leaf("210202", "Fornecedores Estrangeiros EUR", "BAL", "X", "210200"),
    _leaf("210301", "Intercompany DE10", "BAL", "X", "210300"),
    _leaf("210302", "Intercompany FR01", "BAL", "X", "210300"),
    _leaf("220101", "Salarios Diretoria", "BAL", "X", "220100"),
    _leaf("220102", "Salarios Administrativo", "BAL", "X", "220100"),
    _leaf("220103", "Salarios Operacional", "BAL", "X", "220100"),
    _leaf("220201", "Ferias a Pagar", "BAL", "X", "220200"),
    _leaf("220202", "13 Salario a Pagar", "BAL", "X", "220200"),
    _leaf("230101", "Emprestimo Bancario Capital Giro", "BAL", "X", "230000"),
    _leaf("230102", "Financiamento BNDES", "BAL", "X", "230000"),
    _leaf("240101", "ICMS a Recolher", "BAL", "X", "240000"),
    _leaf("240102", "ISS a Recolher", "BAL", "X", "240000"),
    _leaf("250101", "Receita Diferida de Contratos", "BAL", "X", "250000"),
    _leaf("310101", "Capital Social Integralizado", "BAL", "X", "310000"),
    _leaf("310102", "Reserva Legal", "BAL", "X", "310000"),
    _leaf("410101", "Receita Produto Linha Software", "REV", "P", "410100"),
    _leaf("410102", "Receita Produto Linha Hardware", "REV", "P", "410100"),
    _leaf("410201", "Receita Software SaaS", "REV", "P", "410200"),
    _leaf("410202", "Receita Licenciamento Perpetuo", "REV", "P", "410200"),
    _leaf("410301", "Receita Hardware Nacional", "REV", "P", "410300"),
    _leaf("410302", "Receita Hardware Importado", "REV", "P", "410300"),
    _leaf("420101", "Receita Consultoria Implementação", "REV", "P", "420100"),
    _leaf("420102", "Receita Consultoria Treinamento", "REV", "P", "420100"),
    _leaf("420201", "Receita Suporte Mensal", "REV", "P", "420200"),
    _leaf("420202", "Receita Suporte Premium", "REV", "P", "420200"),
    _leaf("430101", "Rendimentos Aplicações Financeiras", "REV", "N", "430000"),
    _leaf("430102", "Variação Cambial Ativa", "REV", "N", "430000"),
    _leaf("510101", "Consumo Matéria Prima Nacional", "MAT", "P", "510100"),
    _leaf("510102", "Consumo Matéria Prima Importada", "MAT", "P", "510100"),
    _leaf("510201", "Mao de Obra Produção", "EXP", "P", "510200"),
    _leaf("510202", "Encargos Produção", "EXP", "P", "510200"),
    _leaf("520101", "Custo Consultoria Alocada", "EXP", "P", "520000"),
    _leaf("520102", "Custo Suporte Técnico", "EXP", "P", "520000"),
    _leaf("530101", "Frete sobre Entregas", "EXP", "P", "530000"),
    _leaf("530102", "Armazenagem e Movimentação", "EXP", "P", "530000"),
    _leaf("610101", "Salarios Diretoria", "EXP", "P", "610100"),
    _leaf("610102", "Salarios Administrativo", "EXP", "P", "610100"),
    _leaf("610103", "Salarios Operacional", "EXP", "P", "610100"),
    _leaf("610201", "Provisao Ferias", "EXP", "P", "610200"),
    _leaf("610202", "Provisao 13 Salario", "EXP", "P", "610200"),
    _leaf("620101", "Aluguel Escritório", "EXP", "P", "620000"),
    _leaf("620102", "Condominio e IPTU", "EXP", "P", "620000"),
    _leaf("620103", "Energia Eletrica", "EXP", "P", "620000"),
    _leaf("630101", "Hospedagem em Nuvem", "EXP", "P", "630100"),
    _leaf("630102", "Infraestrutura Datacenter", "EXP", "P", "630100"),
    _leaf("630201", "Licenças ERP", "EXP", "P", "630200"),
    _leaf("630202", "Licenças BI e Analytics", "EXP", "P", "630200"),
    _leaf("640101", "Mídia Digital", "EXP", "P", "640100"),
    _leaf("640102", "Mídia Offline", "EXP", "P", "640100"),
    _leaf("640201", "Eventos Corporativos", "EXP", "P", "640200"),
    _leaf("640202", "Campanhas Promocionais", "EXP", "P", "640200"),
    _leaf("650101", "Comissões de Vendas", "EXP", "P", "650000"),
    _leaf("650102", "Viagens Comerciais", "EXP", "P", "650000"),
    _leaf("660101", "Serviços Jurídicos", "EXP", "P", "660000"),
    _leaf("660102", "Serviços Auditoria", "EXP", "P", "660000"),
    _leaf("660103", "Serviços Consultoria Externa", "EXP", "P", "660000"),
    ]

    lx_roll, fx_roll = _gather_rollups_from_rows(_rollup_specs_from_sidecar())
    return l4_core + lx_roll, fin_core + fx_roll


LEVEL4_NODES, FINAL_ACCOUNTS = _assemble_detail_accounts()


def build_chart_of_accounts() -> list[dict[str, str]]:
    merged = [*BASE_NODES, *LEVEL3_NODES, *LEVEL4_NODES, *FINAL_ACCOUNTS]
    cnt = Counter(r["GLAccount"] for r in merged)
    dup = sorted(gl for gl, n in cnt.items() if n > 1)
    if dup:
        raise ValueError(f"Contas GL duplicadas ({len(dup)}): {dup[:40]}")
    return [{"ChartOfAccounts": CHART_OF_ACCOUNTS, **row} for row in merged]


def main() -> None:
    repo = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Gera I_GLAccount.csv padronizado para SAP.")
    parser.add_argument("--output", type=Path, default=repo / "data" / "I_GLAccount.csv")
    parser.add_argument("--rows", type=int, default=None, metavar="N", help="Ignorado: plano de contas e fixo.")
    parser.add_argument("--quick", action="store_true", help="Ignorado: plano de contas e fixo.")
    args = parser.parse_args()

    rows = build_chart_of_accounts()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=GLACCOUNT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Escrito {len(rows)} linhas ({len(GLACCOUNT_COLUMNS)} colunas) em {args.output.resolve()}")


if __name__ == "__main__":
    main()
