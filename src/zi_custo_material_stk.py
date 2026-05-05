from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
from faker import Faker

COLUNAS=["CompanyCode","Plant","Material","FiscalYear","FiscalPeriod","TipoMaterial","TipoMaterialText","PlantName","ContaContabil","ContaContabilText","ProfitCenter","CompanyCodeCurrency","BaseUnit","EstoqueQuantidade","EstoqueValorTotal","PrecoUnitario_Oficial"]
DOMINIOS={"CompanyCode":["BR01","US10","DE10","FR01","UK01"],"CompanyCodeCurrency":["BRL","USD","EUR","GBP"],"Plant":["P001","P002","P003","P004"]}

def _v(c,i,r,f):
    if c in DOMINIOS:return str(r.choice(DOMINIOS[c]))
    if "Year" in c:return int(r.integers(2023,2026))
    if "Period" in c:return int(r.integers(1,13))
    if c=="EstoqueQuantidade":return float(np.round(r.uniform(1,12000),3))
    if c in {"EstoqueValorTotal","PrecoUnitario_Oficial"}:return float(np.round(r.uniform(100,800000),2))
    if c=="ContaContabil":return str(r.choice(["510100","510110","130100"]))
    if c in {"PlantName","ContaContabilText","TipoMaterialText","ProfitCenter"}:return f.company()
    return f.word()

def gerar_custo_material_stk(linhas:int=80000,semente:int=42,diretorio_saida:str="data")->Path:
    r=np.random.default_rng(semente)
    f=Faker("pt_BR"); Faker.seed(semente)
    registros=[{c:_v(c,i,r,f) for c in COLUNAS} for i in tqdm(range(linhas),desc="Gerando Custo_Material_STK",unit="linhas")]
    df=pd.DataFrame(registros)
    p=Path(diretorio_saida)/"Custo_Material_STK.csv"; p.parent.mkdir(parents=True,exist_ok=True); df.to_csv(p,index=False); return p

if __name__=="__main__":
    print("[ZI_CUSTO_MATERIAL_STK] Iniciando geracao do CSV...")
    caminho_csv = gerar_custo_material_stk()
    print(f"[ZI_CUSTO_MATERIAL_STK] Geracao concluida com sucesso: {caminho_csv.resolve()}")
