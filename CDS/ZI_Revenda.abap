@AbapCatalog.sqlViewName: 'ZIREVENDA'
@AbapCatalog.compiler.compareFilter: true
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'Relatório de Revenda'
@Metadata.ignorePropagatedAnnotations: true

@VDM.viewType: #COMPOSITE
@Analytics.dataCategory: #CUBE 
@OData.publish: true

define view ZI_Revenda
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
  Geral.ProfitCenter,
  Geral.ProfitCenterName,
  Geral.Plant,
  Geral.PlantName,
  Geral.BusinessArea      as Branch,

  Geral.BaseUnit,
  Geral.Currency,

  @Semantics.amount.currencyCode: 'Currency'
  @DefaultAggregation: #SUM
  Geral.Amount                 as ValorTotal,

  @Semantics.quantity.unitOfMeasure: 'BaseUnit'
  @DefaultAggregation: #SUM
  Geral.Quantity               as Quantidade

}
where
  Geral.Ledger = '0L'
  
