@AbapCatalog.sqlViewName: 'ZIDIVIDENDOS'
@AbapCatalog.compiler.compareFilter: true
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'Relatório de Dividendos a Pagar'
@Metadata.ignorePropagatedAnnotations: true

@VDM.viewType: #COMPOSITE
@Analytics.dataCategory: #CUBE 
@OData.publish: true

define view ZI_Dividendos
  as select from ZI_GLAccountBalanceFlow as Geral
{
  key Geral.CompanyCode,
  key Geral.Ledger,
  key Geral.AccountingDocument                 as DocumentNumber,
  key Geral.LedgerLineItem                     as DocumentItem,
  key Geral.FiscalYear,

  Geral.FiscalPeriod,
  Geral.PostingDate,
  
  Geral.GLAccount,
  Geral.GLAccountName,

  Geral.ProfitCenter,      
  Geral.ProfitCenterName,
  Geral.ControllingArea,
  Geral.BusinessArea      as Branch,
  Geral.Plant,

  Geral.Currency,

  @Semantics.amount.currencyCode: 'Currency'
  @DefaultAggregation: #SUM
  Geral.Amount                 as Valor

}
where
  Geral.Ledger = '0L'
  
  
