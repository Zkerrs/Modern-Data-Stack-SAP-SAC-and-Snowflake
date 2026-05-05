from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
from faker import Faker

COLUNAS=["CompanyCode","Ledger","SourceLedger","AccountingDocument","LedgerLineItem","FiscalYear","GKONT","GKOAR","FiscalPeriod","ChartOfAccounts","GLAccount","GLAccountName","GLAccountType","GLAccountTypeName","GLAccountGroup","AccountGroupName","AccountType","ControllingArea","CostCenter","CostCenterName","ProfitCenter","ProfitCenterName","FunctionalArea","BusinessArea","Segment","Customer","CustomerName","Supplier","SupplierName","MasterFixedAsset","FixedAssetSub","AssetName","AssetTrxType","PostingDate","DocumentDate","NetDueDate","ClearingDate","CreationDate","DocumentType","ItemText","Assignment","ReferenceID","RefDocType","ClearingDoc","Material","MaterialName","Plant","PlantName","SoldProduct","WBSElement","WBSShortID","WBSDescription","Project","HouseBank","HouseBankAccount","DebitCreditCode","Currency","Amount","BaseUnit","Quantity"]

DOMINIOS={"Ledger":["0L","2L","3L"],"SourceLedger":["0L","2L","3L"],"CompanyCode":["BR01","US10","DE10","FR01","UK01"],"ChartOfAccounts":["YCOA","CBR1","CUS1"],"Currency":["BRL","USD","EUR","GBP"],"DebitCreditCode":["S","H"],"DocumentType":["SA","KR","KZ","DZ","DR","RV","WE","RE"],"GLAccountType":["AST","LIA","REV","EXP"],"GLAccountTypeName":["Balance Sheet Account","Non-operating Expense/Income","Primary Costs or Revenue","Secondary Costs"],"ControllingArea":["A000","BR01","US10"],"Segment":["SEGM_A","SEGM_B","SEGM_C"],"Plant":["P001","P002","P003","P004"],"CostCenterName":["Recursos Humanos","TI Global","Vendas Corporativas","Producao Linha 1"],"ItemText":["Pagamento Fornecedor","Faturamento de Venda","Ajuste de Estoque","Folha de Pagamento","Depreciacao Mensal"]}

def _v(c,i,r,f,debit_credit: str | None = None):
    if c in DOMINIOS:return str(r.choice(DOMINIOS[c]))
    if "Date" in c:return f"{int(r.integers(2023,2026)):04d}-{int(r.integers(1,13)):02d}-{int(r.integers(1,29)):02d}"
    if "Year" in c:return int(r.integers(2023,2026))
    if "Period" in c:return int(r.integers(1,13))
    if c=="Amount":
        b=float(np.round(r.uniform(500,250000),2))
        dc = debit_credit if debit_credit is not None else str(r.choice(["S","H"]))
        return b if dc=="S" else -b
    if c=="Quantity":return float(np.round(r.uniform(0,5000),3))
    if c=="GLAccount":return str(r.choice(["110100","120100","210100","3110100","3110200","410100","510110","520100"]))
    if c=="LedgerLineItem":return int(r.integers(1,10))
    if c=="AccountingDocument":return str(int(r.integers(1000000000,1999999999)))
    if c in {"GLAccountName","AccountGroupName","CustomerName","SupplierName","AssetName","MaterialName","PlantName","WBSDescription","ProfitCenterName"}:return f.company()
    if c in {"CostCenter","ProfitCenter","Customer","Supplier","Material","FunctionalArea","BusinessArea"}:return f.bothify(text="??###",letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return f.word()

def gerar_glaccountbalanceflow(linhas:int=300000,semente:int=42,diretorio_saida:str="data")->Path:
    r=np.random.default_rng(semente)
    f=Faker("pt_BR"); Faker.seed(semente)
    registros=[]
    for i in tqdm(range(linhas),desc="Gerando GLAccountBalanceFlow",unit="linhas"):
        dc = str(r.choice(DOMINIOS["DebitCreditCode"]))
        linha = {c:_v(c,i,r,f,debit_credit=dc) for c in COLUNAS}
        linha["DebitCreditCode"] = dc
        registros.append(linha)
    df=pd.DataFrame(registros)
    p=Path(diretorio_saida)/"GLAccountBalanceFlow.csv"; p.parent.mkdir(parents=True,exist_ok=True); df.to_csv(p,index=False); return p

if __name__=="__main__":
    print("[ZI_GLACCOUNTBALANCEFLOW] Iniciando geracao do CSV...")
    caminho_csv = gerar_glaccountbalanceflow()
    print(f"[ZI_GLACCOUNTBALANCEFLOW] Geracao concluida com sucesso: {caminho_csv.resolve()}")
