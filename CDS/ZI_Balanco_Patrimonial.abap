@AbapCatalog.sqlViewName: 'ZIBALANCOFLOW'
@AbapCatalog.compiler.compareFilter: true
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'Relatório do Balanço Patrimonial'
@Metadata.ignorePropagatedAnnotations: true

@VDM.viewType: #COMPOSITE     
@Analytics.dataCategory: #CUBE 
@OData.publish: true

define view ZI_Balanco_Patrimonial
  as select from ZI_GLAccountBalanceFlow as Geral
{
  key Geral.CompanyCode,
  key Geral.Ledger,
  key Geral.AccountingDocument                 as DocumentNumber,
  key Geral.LedgerLineItem                     as DocumentItem,
  key Geral.FiscalYear,

  Geral.FiscalPeriod,
  Geral.PostingDate,
  Geral.DocumentDate,
  Geral.ClearingDate,

  Geral.ChartOfAccounts,
  Geral.GLAccount,
  Geral.GLAccountName,
  Geral.GLAccountType,
  Geral.GLAccountTypeName,
  Geral.GLAccountGroup,
  Geral.AccountGroupName       as GLAccountGroupName, 
  
  Geral.ProfitCenter,
  Geral.ProfitCenterName,
  Geral.CostCenter,
  Geral.CostCenterName,
  Geral.BusinessArea           as Branch,
  Geral.Segment,
  Geral.FunctionalArea,
  Geral.Plant,
  Geral.PlantName,

  Geral.DocumentType           as DocType,
  Geral.ReferenceID            as NotaFiscal_XBLNR,
  Geral.Assignment             as Atribuicao_ZUONR,
  Geral.ItemText               as DocumentText,
  Geral.DebitCreditCode,

  Geral.Currency,


  @Semantics.amount.currencyCode: 'Currency'
  @DefaultAggregation: #SUM
  Geral.Amount                 as AmountInCompanyCurrency

}
where
    Geral.Ledger = '0L'
