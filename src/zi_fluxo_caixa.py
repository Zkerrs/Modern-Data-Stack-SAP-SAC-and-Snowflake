from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
from faker import Faker

COLUNAS=["CompanyCode","Ledger","DocumentNumber","DocumentItem","FiscalYear","FiscalPeriod","PostingDate","DocumentDate","ChartOfAccounts","GLAccount","GLAccountName","GLAccountGroup","AccountGroupName","GLAccountType","GLAccountTypeName","Customer","Supplier","ControllingArea","CostCenter","CostCenterName","ProfitCenter","ProfitCenterName","FunctionalArea","Segment","Branch","Plant","DocType","ItemText","RefDocType","DebitCreditCode","Currency","AmountValue"]

DOMINIOS={
    "Ledger":["0L","2L","3L"],"CompanyCode":["BR01","US10","DE10","FR01","UK01"],"ChartOfAccounts":["YCOA","CBR1","CUS1"],
    "Currency":["BRL","USD","EUR","GBP"],"DebitCreditCode":["S","H"],"DocType":["SA","KR","KZ","DZ","DR","RV","WE","RE"],
    "GLAccountType":["AST","LIA","REV","EXP"],"GLAccountTypeName":["Balance Sheet Account","Non-operating Expense/Income","Primary Costs or Revenue","Secondary Costs"],
    "ControllingArea":["A000","BR01","US10"],"Segment":["SEGM_A","SEGM_B","SEGM_C"],"Plant":["P001","P002","P003","P004"],
    "CostCenterName":["Recursos Humanos","TI Global","Vendas Corporativas","Producao Linha 1"],
    "DocumentText":["Pagamento Fornecedor","Faturamento de Venda","Ajuste de Estoque","Folha de Pagamento","Depreciacao Mensal"],
}

def _v(c,i,r,f,debit_credit: str | None = None):
    if c in DOMINIOS: return str(r.choice(DOMINIOS[c]))
    if "Date" in c:return f"{int(r.integers(2023,2026)):04d}-{int(r.integers(1,13)):02d}-{int(r.integers(1,29)):02d}"
    if "Year" in c:return int(r.integers(2023,2026))
    if "Period" in c:return int(r.integers(1,13))
    if c=="AmountValue":
        b=float(np.round(r.uniform(500,220000),2))
        dc = debit_credit if debit_credit is not None else str(r.choice(DOMINIOS["DebitCreditCode"]))
        return b if dc=="S" else -b
    if c=="GLAccount":return str(r.choice(["110100","120100","210100","3110100","410100","510110"]))
    if c in {"DocumentItem","LedgerLineItem"}:return int(r.integers(1,10))
    if c in {"DocumentNumber","AccountingDocument"}:return str(int(r.integers(1000000000,1999999999)))
    if c=="ItemText":return str(r.choice(DOMINIOS["DocumentText"]))
    if c in {"GLAccountName","AccountGroupName","ProfitCenterName"}:return f.company()
    if c=="CostCenterName":return str(r.choice(DOMINIOS["CostCenterName"]))
    return f.word()

def gerar_fluxo_caixa(linhas:int=120000,semente:int=42,diretorio_saida:str="data")->Path:
    r=np.random.default_rng(semente)
    f=Faker("pt_BR"); Faker.seed(semente)
    registros=[]
    for i in tqdm(range(linhas),desc="Gerando Fluxo_Caixa",unit="linhas"):
        dc = str(r.choice(DOMINIOS["DebitCreditCode"]))
        linha = {c:_v(c,i,r,f,debit_credit=dc) for c in COLUNAS}
        linha["DebitCreditCode"] = dc
        registros.append(linha)
    df=pd.DataFrame(registros)
    p=Path(diretorio_saida)/"Fluxo_Caixa.csv"; p.parent.mkdir(parents=True,exist_ok=True); df.to_csv(p,index=False); return p

if __name__=="__main__":
    print("[ZI_FLUXO_CAIXA] Iniciando geracao do CSV...")
    caminho_csv = gerar_fluxo_caixa()
    print(f"[ZI_FLUXO_CAIXA] Geracao concluida com sucesso: {caminho_csv.resolve()}")
