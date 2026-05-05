@AbapCatalog.sqlViewName: 'ZIPRECOVENDA'
@AbapCatalog.compiler.compareFilter: true
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'Relatório de Preço (Vendas + Impostos)'
@Metadata.ignorePropagatedAnnotations: true

@VDM.viewType: #COMPOSITE
@Analytics.dataCategory: #CUBE 
@OData.publish: true

define view ZI_Preco_Venda
  as select from ZI_GLAccountBalanceFlow as Geral
{
  key Geral.CompanyCode,
  key Geral.Ledger,
  key Geral.AccountingDocument                 as DocumentNumber,
  key Geral.LedgerLineItem                     as DocumentItem,
  key Geral.FiscalYear,

  Geral.FiscalPeriod,
  Geral.PostingDate,

  Geral.Material,
  Geral.Customer,
  Geral.GLAccount,
  Geral.GLAccountName,

  Geral.ControllingArea,
  
  Geral.CostCenter,
  Geral.CostCenterName,
  
  Geral.ProfitCenter,
  Geral.ProfitCenterName,
  
  Geral.Plant,
  Geral.PlantName,
  
  Geral.BusinessArea      as Branch,

  case 
    when Geral.GLAccount like '%31101%' then 'FATURAMENTO BRUTO' 
    when Geral.GLAccount like '%31201%' then 'FATURAMENTO BRUTO' 
    when Geral.GLAccount like '%31102%' then 'DEDUCOES (IMPOSTOS)' 
    else 'OUTROS' 
  end as ComponentePreco,

  Geral.BaseUnit,
  Geral.Currency,

  @Semantics.amount.currencyCode: 'Currency'
  @DefaultAggregation: #SUM
  Geral.Amount                 as ValorTotal,

  @Semantics.quantity.unitOfMeasure: 'BaseUnit'
  @DefaultAggregation: #SUM
  Geral.Quantity               as QuantidadeVenda

}
where
  Geral.Ledger = '0L'
  and ( Geral.GLAccount like '%31101%' 
     or Geral.GLAccount like '%31102%' 
     or Geral.GLAccount like '%31201%' )

  
