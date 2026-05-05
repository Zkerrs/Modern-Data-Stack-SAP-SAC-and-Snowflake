@AbapCatalog.sqlViewName: 'ZIIMPFLOWCB'
@AbapCatalog.compiler.compareFilter: true
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'Relatório de Impostos'
@Metadata.ignorePropagatedAnnotations: true

@VDM.viewType: #COMPOSITE     
@Analytics.dataCategory: #CUBE 
@OData.publish: true

define view ZI_Impostos
  as select from ZI_GLAccountBalanceFlow as Geral
{
  key Geral.CompanyCode,
  key Geral.Ledger,
  key Geral.AccountingDocument,
  key Geral.LedgerLineItem,
  key Geral.FiscalYear,

  Geral.GLAccount,
  Geral.GLAccountName,
  Geral.BusinessArea           as AreaNegocio,
  Geral.Plant                  as Planta,
  Geral.Supplier,
  Geral.SupplierName,
  Geral.Customer,
  Geral.CustomerName,
  Geral.ProfitCenter,
  Geral.ProfitCenterName,

  Geral.DocumentType,
  Geral.ReferenceID            as NotaFiscal_XBLNR,
  Geral.ItemText               as Historico,
  Geral.Assignment             as Atribuicao,

  Geral.PostingDate            as DataLancamento,
  Geral.DocumentDate           as DataDocumento,
  Geral.ClearingDate           as DataCompensacao,

  case 
    when Geral.ClearingDoc is not null and Geral.ClearingDoc <> '' 
    then 'Recolhido/Compensado'
    else 'Aberto/A Recolher'
  end                          as StatusImposto,

  @Semantics.currencyCode: true
  Geral.Currency               as CompanyCodeCurrency,

  @Semantics.amount.currencyCode: 'CompanyCodeCurrency'
  @DefaultAggregation: #SUM
  Geral.Amount                 as AmountInCompanyCodeCurrency,

  
  -- Valor Débito (Recuperável)
  @Semantics.amount.currencyCode: 'CompanyCodeCurrency'
  @DefaultAggregation: #SUM
  case 
    when Geral.DebitCreditCode = 'S' 
    then Geral.Amount
    else cast( 0 as abap.curr(23,2) )
  end                          as ValorDebito,

  -- Valor Crédito (A Recolher)
  @Semantics.amount.currencyCode: 'CompanyCodeCurrency'
  @DefaultAggregation: #SUM
  case 
    when Geral.DebitCreditCode = 'H' 
    then Geral.Amount * -1
    else cast( 0 as abap.curr(23,2) )
  end                          as ValorCredito

}
where
    Geral.Ledger = '0L'
    and Geral.AccountType = 'S'
