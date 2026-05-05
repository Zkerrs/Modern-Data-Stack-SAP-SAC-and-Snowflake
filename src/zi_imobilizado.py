from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
from faker import Faker

COLUNAS=["CompanyCode","Ledger","AccountingDocument","LedgerLineItem","FiscalYear","AssetMainNumber","AssetSubNumber","AssetName","AssetClass","AssetClassDescription","AssetTrxType","AssetTransactionTypeName","FiscalPeriod","PostingDate","DocumentDate","ReferenceID","ItemText","CostCenter","CostCenterName","ProfitCenter","ProfitCenterName","Segment","Plant","PlantName","WBSElement","WBSDescription","Project","GLAccount","GLAccountName","Supplier","SupplierName","Currency","Amount"]
DOMINIOS={"Ledger":["0L","2L","3L"],"CompanyCode":["BR01","US10","DE10","FR01","UK01"],"Currency":["BRL","USD","EUR","GBP"],"Segment":["SEGM_A","SEGM_B","SEGM_C"],"Plant":["P001","P002","P003","P004"],"CostCenterName":["Recursos Humanos","TI Global","Vendas Corporativas","Producao Linha 1"],"ItemText":["Pagamento Fornecedor","Faturamento de Venda","Ajuste de Estoque","Folha de Pagamento","Depreciacao Mensal"]}

def _v(c,i,r,f):
    if c in DOMINIOS:return str(r.choice(DOMINIOS[c]))
    if "Date" in c:return f"{int(r.integers(2023,2026)):04d}-{int(r.integers(1,13)):02d}-{int(r.integers(1,29)):02d}"
    if "Year" in c:return int(r.integers(2023,2026))
    if "Period" in c:return int(r.integers(1,13))
    if c=="Amount":return float(np.round(r.uniform(-300000,300000),2))
    if c=="GLAccount":return str(r.choice(["150100","150110","150120","150190","530100"]))
    if c=="LedgerLineItem":return int(r.integers(1,10))
    if c=="AccountingDocument":return str(int(r.integers(1000000000,1999999999)))
    if c in {"AssetName","AssetClassDescription","AssetTransactionTypeName","ProfitCenterName","PlantName","WBSDescription","GLAccountName","SupplierName"}:return f.company()
    return f.word()

def gerar_imobilizado(linhas:int=90000,semente:int=42,diretorio_saida:str="data")->Path:
    r=np.random.default_rng(semente)
    f=Faker("pt_BR"); Faker.seed(semente)
    registros=[{c:_v(c,i,r,f) for c in COLUNAS} for i in tqdm(range(linhas),desc="Gerando Imobilizado",unit="linhas")]
    df=pd.DataFrame(registros)
    p=Path(diretorio_saida)/"Imobilizado.csv"; p.parent.mkdir(parents=True,exist_ok=True); df.to_csv(p,index=False); return p

if __name__=="__main__":
    print("[ZI_IMOBILIZADO] Iniciando geracao do CSV...")
    caminho_csv = gerar_imobilizado()
    print(f"[ZI_IMOBILIZADO] Geracao concluida com sucesso: {caminho_csv.resolve()}")
