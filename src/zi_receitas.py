from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
from faker import Faker

COLUNAS=["CompanyCode","Ledger","DocumentNumber","DocumentItem","FiscalYear","ChartOfAccounts","GLAccount","GLAccountName","GLAccountType","GLAccountTypeName","GLAccountGroup","GLAccountGroupName","ControllingArea","ProfitCenter","ProfitCenterName","Segment","Branch","Customer","CustomerName","Material","MaterialName","Plant","PlantName","SoldProduct","PostingDate","DocumentDate","FiscalPeriod","DocType","DocumentText","Atribuicao_ZUONR","NotaFiscal_XBLNR","Unit","SoldQuantity","Currency","DebitCredit","AmountLocalCurrency"]
DOMINIOS={"Ledger":["0L","2L","3L"],"CompanyCode":["BR01","US10","DE10","FR01","UK01"],"ChartOfAccounts":["YCOA","CBR1","CUS1"],"Currency":["BRL","USD","EUR","GBP"],"DebitCredit":["S","H"],"DocType":["SA","KR","KZ","DZ","DR","RV","WE","RE"],"GLAccountType":["AST","LIA","REV","EXP"],"GLAccountTypeName":["Balance Sheet Account","Non-operating Expense/Income","Primary Costs or Revenue","Secondary Costs"],"ControllingArea":["A000","BR01","US10"],"Segment":["SEGM_A","SEGM_B","SEGM_C"],"Plant":["P001","P002","P003","P004"],"DocumentText":["Pagamento Fornecedor","Faturamento de Venda","Ajuste de Estoque","Folha de Pagamento","Depreciacao Mensal"]}

def _v(c,i,r,f,debit_credit: str | None = None):
    if c in DOMINIOS:return str(r.choice(DOMINIOS[c]))
    if "Date" in c:return f"{int(r.integers(2023,2026)):04d}-{int(r.integers(1,13)):02d}-{int(r.integers(1,29)):02d}"
    if "Year" in c:return int(r.integers(2023,2026))
    if "Period" in c:return int(r.integers(1,13))
    if c=="SoldQuantity":return float(np.round(r.uniform(1,5000),3))
    if c=="AmountLocalCurrency":
        b=float(np.round(r.uniform(500,220000),2))
        dc = debit_credit if debit_credit is not None else str(r.choice(DOMINIOS["DebitCredit"]))
        return b if dc=="S" else -b
    if c=="GLAccount":return str(r.choice(["3110100","3120100","410100","410110"]))
    if c=="DocumentItem":return int(r.integers(1,10))
    if c=="DocumentNumber":return str(int(r.integers(1000000000,1999999999)))
    if c in {"GLAccountName","GLAccountGroupName","ProfitCenterName","CustomerName","MaterialName","PlantName"}:return f.company()
    return f.word()

def gerar_receitas(linhas:int=120000,semente:int=42,diretorio_saida:str="data")->Path:
    r=np.random.default_rng(semente)
    f=Faker("pt_BR"); Faker.seed(semente)
    registros=[]
    for i in tqdm(range(linhas),desc="Gerando Receitas",unit="linhas"):
        dc = str(r.choice(DOMINIOS["DebitCredit"]))
        linha = {c:_v(c,i,r,f,debit_credit=dc) for c in COLUNAS}
        linha["DebitCredit"] = dc
        registros.append(linha)
    df=pd.DataFrame(registros)
    p=Path(diretorio_saida)/"Receitas.csv"; p.parent.mkdir(parents=True,exist_ok=True); df.to_csv(p,index=False); return p

if __name__=="__main__":
    print("[ZI_RECEITAS] Iniciando geracao do CSV...")
    caminho_csv = gerar_receitas()
    print(f"[ZI_RECEITAS] Geracao concluida com sucesso: {caminho_csv.resolve()}")
