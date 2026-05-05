@AbapCatalog.sqlViewName: 'ZIRECEITAS'
@AbapCatalog.compiler.compareFilter: true
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'Relatório de Receitas (Faturamento/DRE)'
@Metadata.ignorePropagatedAnnotations: true

@VDM.viewType: #COMPOSITE
@Analytics.dataCategory: #CUBE
@OData.publish: true

define view ZI_Receitas
  as select from ZI_GLAccountBalanceFlow as Geral
{
  key Geral.CompanyCode,
  key Geral.Ledger,
  key Geral.AccountingDocument as DocumentNumber,
  key Geral.LedgerLineItem     as DocumentItem,
  key Geral.FiscalYear,

      Geral.ChartOfAccounts,
      Geral.GLAccount,
      Geral.GLAccountName,
      Geral.GLAccountType,
      Geral.GLAccountTypeName,
      Geral.GLAccountGroup,
      Geral.AccountGroupName,

      Geral.ControllingArea,
      Geral.ProfitCenter,
      Geral.ProfitCenterName,
      Geral.Segment,
      Geral.BusinessArea       as Branch,

      Geral.Customer,
      Geral.CustomerName,
      Geral.Material,
      Geral.MaterialName,
      Geral.Plant,
      Geral.PlantName,
      Geral.SoldProduct,

      Geral.PostingDate,
      Geral.DocumentDate,
      Geral.FiscalPeriod,

      Geral.DocumentType       as DocType,
      Geral.ItemText           as DocumentText,
      Geral.Assignment         as Atribuicao_ZUONR,
      Geral.ReferenceID        as NotaFiscal_XBLNR,

      Geral.BaseUnit           as Unit,
      @Semantics.quantity.unitOfMeasure: 'Unit'
      @DefaultAggregation: #SUM
      Geral.Quantity           as SoldQuantity,

      -- --- VALORES ---
      Geral.Currency,
      Geral.DebitCreditCode    as DebitCredit,

      @Semantics.amount.currencyCode: 'Currency'
      @DefaultAggregation: #SUM
      Geral.Amount * -1        as AmountLocalCurrency
}
where
      Geral.Ledger          = '0L'
  and ( Geral.GLAccountType = 'P'     or Geral.GLAccountType = 'N' )
  and ( Geral.CostCenter    is null   or Geral.CostCenter    = ''  )
  and Geral.ProfitCenter    is not null
