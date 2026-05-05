@AbapCatalog.sqlViewName: 'ZIMATBOP'
@AbapCatalog.compiler.compareFilter: true
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'Relatório Material BOP'
@Metadata.ignorePropagatedAnnotations: true

@VDM.viewType: #COMPOSITE     
@Analytics.dataCategory: #CUBE 
@OData.publish: true

define view ZI_Material_Bop
  as select from ZI_GLAccountBalanceFlow as Geral

  left outer join I_ProductValuationBasic as Custo on  Geral.Material = Custo.Product
                                                   and Geral.Plant    = Custo.ValuationArea
                                                   and Custo.ValuationType = ''
    
  left outer join I_Product as TipoMaterial        on Geral.Material = TipoMaterial.Product 
{
  key Geral.CompanyCode,
  key Geral.Ledger,
  key Geral.FiscalYear,
  key Geral.AccountingDocument,
  key Geral.LedgerLineItem,

  Geral.Material,
  Geral.MaterialName,
  
  TipoMaterial.ProductType   as TipoMaterial,
  
  Geral.Plant,
  Geral.Supplier,
  Geral.SupplierName,
  
  Geral.GLAccount              as ContaContabil,
  Geral.GLAccountName,
  Geral.CostCenter             as CentroCusto,
  Geral.CostCenterName,
  Geral.ProfitCenter           as CentroLucro,
  Geral.ProfitCenterName,

  Custo.InventoryValuationProcedure as TipoPreco,

  Geral.PostingDate            as DataLancamento,
  Geral.FiscalPeriod,
  Geral.DocumentType,
  Geral.ItemText               as Historico,

  @Semantics.currencyCode: true
  Geral.Currency               as CompanyCodeCurrency,

  @Semantics.amount.currencyCode: 'CompanyCodeCurrency'
  @DefaultAggregation: #SUM
  Geral.Amount * (-1)          as AmountValue, 

  @Semantics.amount.currencyCode: 'CompanyCodeCurrency'
  @DefaultAggregation: #SUM
  case 
    when Geral.DebitCreditCode = 'S' 
    then Geral.Amount * (-1)
    else cast( 0 as abap.curr(23,2) )
  end                          as ValorEntrada_Compras,

  @Semantics.amount.currencyCode: 'CompanyCodeCurrency'
  @DefaultAggregation: #SUM
  case 
    when Geral.DebitCreditCode = 'H' 
    then Geral.Amount * (-1)  
    else cast( 0 as abap.curr(23,2) )
  end                          as ValorSaida_Consumo,

  @Semantics.unitOfMeasure: true
  Geral.BaseUnit               as BaseUnit,

  @Semantics.quantity.unitOfMeasure: 'BaseUnit'
  @DefaultAggregation: #SUM
  Geral.Quantity * (-1)        as QuantidadeTotal

}
where
      Geral.Ledger      = '0L'
  and Geral.AccountType = 'S'
  and Geral.Material    is not null 
  and Geral.Material    <> ''
