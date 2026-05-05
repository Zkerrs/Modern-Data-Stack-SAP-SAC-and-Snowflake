@AbapCatalog.sqlViewName: 'ZIROYALTIES'
@AbapCatalog.compiler.compareFilter: true
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'Relatório de Royalties'
@Metadata.ignorePropagatedAnnotations: true

@VDM.viewType: #COMPOSITE
@Analytics.dataCategory: #CUBE 
@OData.publish: true

define view ZI_Royalties
  as select from ZI_GLAccountBalanceFlow as Geral
{
  key Geral.CompanyCode,
  key Geral.Ledger,
  key Geral.AccountingDocument                 as DocumentNumber,
  key Geral.LedgerLineItem                     as DocumentItem,
  key Geral.FiscalYear,

  Geral.FiscalPeriod,
  Geral.PostingDate,
  
  Geral.Supplier,
  Geral.SupplierName,
  
  Geral.Material,
  Geral.MaterialName,

  Geral.GLAccount,
  Geral.GLAccountName,
  
  Geral.CostCenter,
  Geral.CostCenterName,
  Geral.ProfitCenter,
  Geral.ProfitCenterName,

  Geral.Assignment         as Atribuicao,
  Geral.ItemText           as Historico,
  Geral.ReferenceID        as Referencia,

  Geral.Currency,

  @Semantics.amount.currencyCode: 'Currency'
  @DefaultAggregation: #SUM
  Geral.Amount                 as Valor

}
where
  Geral.Ledger = '0L'
