from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
from faker import Faker

COLUNAS=["CompanyCode","Ledger","DocumentNumber","DocumentItem","FiscalYear","ChartOfAccounts","GLAccount","GLAccountName","GLAccountType","GLAccountTypeName","GLAccountGroup","AccountGroupName","ControllingArea","CostCenter","CostCenterName","ProfitCenter","ProfitCenterName","FunctionalArea","Branch","Supplier","SupplierName","Material","MaterialName","PostingDate","DocumentDate","FiscalPeriod","DocType","DocumentText","Atribuicao_ZUONR","NotaFiscal_XBLNR","WBSElement","WBSDescription","Currency","DebitCredit","AmountLocalCurrency"]

DOMINIOS={"Ledger":["0L","2L","3L"],"CompanyCode":["BR01","US10","DE10","FR01","UK01"],"ChartOfAccounts":["YCOA","CBR1","CUS1"],"Currency":["BRL","USD","EUR","GBP"],"DebitCredit":["S","H"],"DocType":["SA","KR","KZ","DZ","DR","RV","WE","RE"],"GLAccountType":["AST","LIA","REV","EXP"],"GLAccountTypeName":["Balance Sheet Account","Non-operating Expense/Income","Primary Costs or Revenue","Secondary Costs"],"ControllingArea":["A000","BR01","US10"],"Segment":["SEGM_A","SEGM_B","SEGM_C"],"Plant":["P001","P002","P003","P004"],"CostCenterName":["Recursos Humanos","TI Global","Vendas Corporativas","Producao Linha 1"],"DocumentText":["Pagamento Fornecedor","Faturamento de Venda","Ajuste de Estoque","Folha de Pagamento","Depreciacao Mensal"]}

def _v(c,i,r,f,debit_credit: str | None = None):
    if c in DOMINIOS:return str(r.choice(DOMINIOS[c]))
    if "Date" in c:return f"{int(r.integers(2023,2026)):04d}-{int(r.integers(1,13)):02d}-{int(r.integers(1,29)):02d}"
    if "Year" in c:return int(r.integers(2023,2026))
    if "Period" in c:return int(r.integers(1,13))
    if c=="AmountLocalCurrency":
        b=float(np.round(r.uniform(500,130000),2))
        dc = debit_credit if debit_credit is not None else str(r.choice(DOMINIOS["DebitCredit"]))
        return b if dc=="S" else -b
    if c=="GLAccount":return str(r.choice(["510100","510110","520100","530100","540100","550100"]))
    if c=="DocumentItem":return int(r.integers(1,10))
    if c=="DocumentNumber":return str(int(r.integers(1000000000,1999999999)))
    if c in {"GLAccountName","AccountGroupName","ProfitCenterName","SupplierName","MaterialName","WBSDescription"}:return f.company()
    if c=="CostCenterName":return str(r.choice(DOMINIOS["CostCenterName"]))
    if c in {"CostCenter","ProfitCenter","Material","Supplier","Branch"}:return f.bothify(text="??###",letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return f.word()

def gerar_despesas(linhas:int=100000,semente:int=42,diretorio_saida:str="data")->Path:
    r=np.random.default_rng(semente)
    f=Faker("pt_BR"); Faker.seed(semente)
    registros=[]
    for i in tqdm(range(linhas),desc="Gerando Despesas",unit="linhas"):
        dc = str(r.choice(DOMINIOS["DebitCredit"]))
        linha = {c:_v(c,i,r,f,debit_credit=dc) for c in COLUNAS}
        linha["DebitCredit"] = dc
        registros.append(linha)
    df=pd.DataFrame(registros)
    p=Path(diretorio_saida)/"Despesas.csv"; p.parent.mkdir(parents=True,exist_ok=True); df.to_csv(p,index=False); return p

if __name__=="__main__":
    print("[ZI_DESPESAS] Iniciando geracao do CSV...")
    caminho_csv = gerar_despesas()
    print(f"[ZI_DESPESAS] Geracao concluida com sucesso: {caminho_csv.resolve()}")
