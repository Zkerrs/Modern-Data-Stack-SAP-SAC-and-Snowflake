from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
from faker import Faker

COLUNAS=["CompanyCode","Ledger","DocumentNumber","DocumentItem","FiscalYear","FiscalPeriod","PostingDate","Supplier","SupplierName","Material","MaterialName","GLAccount","GLAccountName","CostCenter","CostCenterName","ProfitCenter","ProfitCenterName","Atribuicao","Historico","Referencia","Currency","Valor"]
DOMINIOS={"Ledger":["0L","2L","3L"],"CompanyCode":["BR01","US10","DE10","FR01","UK01"],"Currency":["BRL","USD","EUR","GBP"],"CostCenterName":["Recursos Humanos","TI Global","Vendas Corporativas","Producao Linha 1"],"DocumentText":["Pagamento Fornecedor","Faturamento de Venda","Ajuste de Estoque","Folha de Pagamento","Depreciacao Mensal"]}

def _v(c,i,r,f):
    if c in DOMINIOS:return str(r.choice(DOMINIOS[c]))
    if "Date" in c:return f"{int(r.integers(2023,2026)):04d}-{int(r.integers(1,13)):02d}-{int(r.integers(1,29)):02d}"
    if "Year" in c:return int(r.integers(2023,2026))
    if "Period" in c:return int(r.integers(1,13))
    if c=="Valor":return float(np.round(r.uniform(-120000,120000),2))
    if c=="GLAccount":return str(r.choice(["430100","430110","550100"]))
    if c=="DocumentItem":return int(r.integers(1,10))
    if c=="DocumentNumber":return str(int(r.integers(1000000000,1999999999)))
    if c=="Historico":return str(r.choice(DOMINIOS["DocumentText"]))
    if c in {"SupplierName","MaterialName","GLAccountName","ProfitCenterName"}:return f.company()
    return f.word()

def gerar_royalties(linhas:int=70000,semente:int=42,diretorio_saida:str="data")->Path:
    r=np.random.default_rng(semente)
    f=Faker("pt_BR"); Faker.seed(semente)
    registros=[{c:_v(c,i,r,f) for c in COLUNAS} for i in tqdm(range(linhas),desc="Gerando Royalties",unit="linhas")]
    df=pd.DataFrame(registros)
    p=Path(diretorio_saida)/"Royalties.csv"; p.parent.mkdir(parents=True,exist_ok=True); df.to_csv(p,index=False); return p

if __name__=="__main__":
    print("[ZI_ROYALTIES] Iniciando geracao do CSV...")
    caminho_csv = gerar_royalties()
    print(f"[ZI_ROYALTIES] Geracao concluida com sucesso: {caminho_csv.resolve()}")
