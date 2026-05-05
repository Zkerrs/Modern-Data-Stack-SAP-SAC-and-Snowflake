@AbapCatalog.sqlViewName: 'ZICUSTOMATSTK'
@AbapCatalog.compiler.compareFilter: true
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'Relatório de Custo Material'
@Metadata.ignorePropagatedAnnotations: true
@VDM.viewType: #COMPOSITE     
@Analytics.dataCategory: #CUBE 

define view ZI_Custo_Material_STK
  as select from ZI_Custo_Mat_Base as Base

{
  key Base.CompanyCode,
  key Base.Plant,
  key Base.Material,
  key Base.FiscalYear,
  key Base.FiscalPeriod,

  Base.TipoMaterial,
  Base.TipoMaterialText,
  Base.PlantName,
  Base.ContaContabil, 
  Base.ContaContabilText,
  Base.ProfitCenter,

  @Semantics.currencyCode: true
  Base.CompanyCodeCurrency,
  
  @Semantics.unitOfMeasure: true
  Base.BaseUnit,


  // Quantidade: SOMA
  @DefaultAggregation: #SUM
  sum( Base.QtdBruta ) as EstoqueQuantidade,

  // Valor Total: SOMA (Soma o valor que já veio calculado)
  @Semantics.amount.currencyCode: 'CompanyCodeCurrency'
  @DefaultAggregation: #SUM
  sum( Base.ValorTotalCalculado ) as EstoqueValorTotal,

  // Preço Unitário: MÁXIMO (Fixa o valor)
  @EndUserText.label: 'Preço Unitário'
  @Semantics.amount.currencyCode: 'CompanyCodeCurrency'
  @DefaultAggregation: #MAX  
  max( Base.PrecoUnitarioBruto ) as PrecoUnitario_Oficial

}

group by
  Base.CompanyCode,
  Base.Plant,
  Base.Material,
  Base.FiscalYear,
  Base.FiscalPeriod,
  Base.TipoMaterial,
  Base.TipoMaterialText,
  Base.PlantName,
  Base.ContaContabil,
  Base.ContaContabilText,
  Base.ProfitCenter,
  Base.CompanyCodeCurrency,
  Base.BaseUnit
