from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
from faker import Faker

COLUNAS=["CompanyCode","Ledger","AccountingDocument","LedgerLineItem","FiscalYear","GLAccount","GLAccountName","AreaNegocio","Planta","Supplier","SupplierName","Customer","CustomerName","ProfitCenter","ProfitCenterName","DocumentType","NotaFiscal_XBLNR","Historico","Atribuicao","DataLancamento","DataDocumento","DataCompensacao","StatusImposto","CompanyCodeCurrency","AmountInCompanyCodeCurrency","ValorDebito","ValorCredito"]
DOMINIOS={"Ledger":["0L","2L","3L"],"CompanyCode":["BR01","US10","DE10","FR01","UK01"],"CompanyCodeCurrency":["BRL","USD","EUR","GBP"],"DocumentType":["SA","KR","KZ","DZ","DR","RV","WE","RE"],"StatusImposto":["Aberto/A Recolher","Recolhido/Compensado"],"DocumentText":["Pagamento Fornecedor","Faturamento de Venda","Ajuste de Estoque","Folha de Pagamento","Depreciacao Mensal"]}

def _v(c,i,r,f):
    if c in DOMINIOS:return str(r.choice(DOMINIOS[c]))
    if c.startswith("Data"):return f"{int(r.integers(2023,2026)):04d}-{int(r.integers(1,13)):02d}-{int(r.integers(1,29)):02d}"
    if "Year" in c:return int(r.integers(2023,2026))
    if c in {"AmountInCompanyCodeCurrency","ValorDebito","ValorCredito"}:return float(np.round(r.uniform(0,90000),2))
    if c=="GLAccount":return str(r.choice(["140100","140110","240100","240110","540100"]))
    if c=="LedgerLineItem":return int(r.integers(1,10))
    if c=="AccountingDocument":return str(int(r.integers(1000000000,1999999999)))
    if c=="Historico":return str(r.choice(DOMINIOS["DocumentText"]))
    if c in {"GLAccountName","SupplierName","CustomerName","ProfitCenterName"}:return f.company()
    return f.word()

def gerar_impostos(linhas:int=100000,semente:int=42,diretorio_saida:str="data")->Path:
    r=np.random.default_rng(semente)
    f=Faker("pt_BR"); Faker.seed(semente)
    registros=[{c:_v(c,i,r,f) for c in COLUNAS} for i in tqdm(range(linhas),desc="Gerando Impostos",unit="linhas")]
    df=pd.DataFrame(registros)
    p=Path(diretorio_saida)/"Impostos.csv"; p.parent.mkdir(parents=True,exist_ok=True); df.to_csv(p,index=False); return p

if __name__=="__main__":
    print("[ZI_IMPOSTOS] Iniciando geracao do CSV...")
    caminho_csv = gerar_impostos()
    print(f"[ZI_IMPOSTOS] Geracao concluida com sucesso: {caminho_csv.resolve()}")
