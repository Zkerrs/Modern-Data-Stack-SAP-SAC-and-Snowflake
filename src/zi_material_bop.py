from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
from faker import Faker

COLUNAS=["CompanyCode","Ledger","FiscalYear","AccountingDocument","LedgerLineItem","Material","MaterialName","TipoMaterial","Plant","Supplier","SupplierName","ContaContabil","GLAccountName","CentroCusto","CostCenterName","CentroLucro","ProfitCenterName","TipoPreco","DataLancamento","FiscalPeriod","DocumentType","Historico","CompanyCodeCurrency","AmountValue","ValorEntrada_Compras","ValorSaida_Consumo","BaseUnit","QuantidadeTotal"]
DOMINIOS={"Ledger":["0L","2L","3L"],"CompanyCode":["BR01","US10","DE10","FR01","UK01"],"CompanyCodeCurrency":["BRL","USD","EUR","GBP"],"DocumentType":["SA","KR","KZ","DZ","DR","RV","WE","RE"],"Plant":["P001","P002","P003","P004"],"CostCenterName":["Recursos Humanos","TI Global","Vendas Corporativas","Producao Linha 1"],"DocumentText":["Pagamento Fornecedor","Faturamento de Venda","Ajuste de Estoque","Folha de Pagamento","Depreciacao Mensal"]}

def _v(c,i,r,f):
    if c in DOMINIOS:return str(r.choice(DOMINIOS[c]))
    if c=="DataLancamento":return f"{int(r.integers(2023,2026)):04d}-{int(r.integers(1,13)):02d}-{int(r.integers(1,29)):02d}"
    if "Year" in c:return int(r.integers(2023,2026))
    if "Period" in c:return int(r.integers(1,13))
    if c in {"AmountValue","ValorEntrada_Compras","ValorSaida_Consumo"}:return float(np.round(r.uniform(-100000,100000),2))
    if c=="QuantidadeTotal":return float(np.round(r.uniform(0,5000),3))
    if c in {"ContaContabil"}:return str(r.choice(["510100","510110","130100"]))
    if c=="LedgerLineItem":return int(r.integers(1,10))
    if c=="AccountingDocument":return str(int(r.integers(1000000000,1999999999)))
    if c=="Historico":return str(r.choice(DOMINIOS["DocumentText"]))
    if c in {"MaterialName","SupplierName","GLAccountName","ProfitCenterName"}:return f.company()
    return f.word()

def gerar_material_bop(linhas:int=90000,semente:int=42,diretorio_saida:str="data")->Path:
    r=np.random.default_rng(semente)
    f=Faker("pt_BR"); Faker.seed(semente)
    registros=[{c:_v(c,i,r,f) for c in COLUNAS} for i in tqdm(range(linhas),desc="Gerando Material_Bop",unit="linhas")]
    df=pd.DataFrame(registros)
    p=Path(diretorio_saida)/"Material_Bop.csv"; p.parent.mkdir(parents=True,exist_ok=True); df.to_csv(p,index=False); return p

if __name__=="__main__":
    print("[ZI_MATERIAL_BOP] Iniciando geracao do CSV...")
    caminho_csv = gerar_material_bop()
    print(f"[ZI_MATERIAL_BOP] Geracao concluida com sucesso: {caminho_csv.resolve()}")
