@AbapCatalog.sqlViewName: 'ZIFLUXCAIX'
@AbapCatalog.compiler.compareFilter: true
@AbapCatalog.preserveKey: true
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'Relatório Fluxo de Caixa'

@VDM.viewType: #COMPOSITE
@Analytics.dataCategory: #CUBE
@OData.publish: true

define view ZI_Fluxo_Caixa
  as select from ZI_GLAccountBalanceFlow
  
{
  key CompanyCode,
  key Ledger,
  key AccountingDocument                 as DocumentNumber,
  key LedgerLineItem                     as DocumentItem,
  key FiscalYear,

  FiscalPeriod,
  PostingDate,
  DocumentDate,

  ChartOfAccounts,
  GLAccount,
  GLAccountName,
  
  GLAccountGroup,
  AccountGroupName,

  GLAccountType,
  GLAccountTypeName,

  Customer,
  Supplier,

  ControllingArea,
  CostCenter,
  CostCenterName,
  ProfitCenter,
  ProfitCenterName,
  FunctionalArea,
  Segment,
  BusinessArea           as Branch,
  Plant,

  DocumentType           as DocType,
  ItemText,
  RefDocType,
  DebitCreditCode,       

  Currency,

  @Semantics.amount.currencyCode: 'Currency'
  @DefaultAggregation: #SUM
  Amount                 as AmountValue

}
where
  Ledger = '0L'
