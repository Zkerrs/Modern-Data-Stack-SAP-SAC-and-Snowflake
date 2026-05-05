@AbapCatalog.sqlViewName: 'ZIDESPESAS'
@AbapCatalog.compiler.compareFilter: true
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'Relatório de Despesas (DRE)'
@Metadata.ignorePropagatedAnnotations: true

@VDM.viewType: #COMPOSITE     
@Analytics.dataCategory: #CUBE 
@OData.publish: true

define view ZI_Despesas
  as select from ZI_GLAccountBalanceFlow as Geral
{
  key Geral.CompanyCode,
  key Geral.Ledger,
  key Geral.AccountingDocument                 as DocumentNumber,
  key Geral.LedgerLineItem                     as DocumentItem,
  key Geral.FiscalYear,

      Geral.ChartOfAccounts,
      Geral.GLAccount,
      Geral.GLAccountName,
      Geral.GLAccountType,
      Geral.GLAccountTypeName,
      Geral.GLAccountGroup,
      Geral.AccountGroupName,

      Geral.ControllingArea,
      Geral.CostCenter,
      Geral.CostCenterName,
      Geral.ProfitCenter,
      Geral.ProfitCenterName,
      Geral.FunctionalArea,
      Geral.BusinessArea                       as Branch,

      Geral.Supplier,
      Geral.SupplierName,
      Geral.Material,
      Geral.MaterialName,

      Geral.PostingDate,
      Geral.DocumentDate,
      Geral.FiscalPeriod,

      -- --- DOCUMENTAÇÃO ---
      Geral.DocumentType                       as DocType,
      Geral.ItemText                           as DocumentText,
      Geral.Assignment                         as Atribuicao_ZUONR,
      Geral.ReferenceID                        as NotaFiscal_XBLNR,

      Geral.WBSElement,
      Geral.WBSDescription,

      -- --- VALORES ---
      Geral.Currency,
      Geral.DebitCreditCode                    as DebitCredit,

      @Semantics.amount.currencyCode: 'Currency'
      @DefaultAggregation: #SUM
      Geral.Amount                             as AmountLocalCurrency
}
where
      Geral.Ledger = '0L'
  and ( Geral.GLAccountType = 'P' or Geral.GLAccountType = 'S' )
  and Geral.CostCenter is not null
  and Geral.CostCenter <> ''
