@AbapCatalog.sqlViewName: 'ZICUSTOMATBASE'
@AbapCatalog.compiler.compareFilter: true
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'Base de Cálculo do Custo Material'
@Metadata.ignorePropagatedAnnotations: true
@VDM.viewType: #COMPOSITE     

define view ZI_Custo_Mat_Base
  as select from I_MaterialStock_2 as Historico

  left outer join I_ProductValuationBasic as Mestre   on  Historico.Material      = Mestre.Product
                                                      and Historico.Plant         = Mestre.ValuationArea
                                                      and Mestre.ValuationType    = ''

  left outer join I_ProductPlant as DadosPlanta       on  Historico.Material      = DadosPlanta.Product
                                                      and Historico.Plant         = DadosPlanta.Plant

  left outer join I_Product as TipoMaterial           on Historico.Material = TipoMaterial.Product 

  left outer join I_ProductTypeText as TextoTipo      on  TipoMaterial.ProductType = TextoTipo.ProductType
                                                      and TextoTipo.Language       = $session.system_language
    
  left outer join I_Plant as Planta                   on Historico.Plant = Planta.Plant
    
  left outer join I_CompanyCode as Empresa            on Historico.CompanyCode = Empresa.CompanyCode

  left outer join t030 as RContabil                   on  Empresa.ChartOfAccounts    = RContabil.ktopl
                                                      and Mestre.ValuationClass      = RContabil.bklas
                                                      and RContabil.ktosl            = 'BSX'

  left outer join I_GLAccountText as TextoConta       on  RContabil.konts         = TextoConta.GLAccount
                                                      and Empresa.ChartOfAccounts = TextoConta.ChartOfAccounts
                                                      and TextoConta.Language     = $session.system_language

{
  key Historico.CompanyCode,
  key Historico.Plant,
  key Historico.Material,

  key substring( cast(Historico.MatlDocLatestPostgDate as abap.char(8)), 1, 4 ) as FiscalYear,
  key substring( cast(Historico.MatlDocLatestPostgDate as abap.char(8)), 5, 2 ) as FiscalPeriod,
  
  TipoMaterial.ProductType           as TipoMaterial,
  TextoTipo.MaterialTypeName         as TipoMaterialText,
  Planta.PlantName,
  RContabil.konts                    as ContaContabil, 
  TextoConta.GLAccountName           as ContaContabilText,
  DadosPlanta.ProfitCenter,
  
  Historico._CompanyCode.Currency    as CompanyCodeCurrency,
  Historico.MaterialBaseUnit         as BaseUnit,

  
  // Quantidade
  Historico.MatlWrhsStkQtyInMatlBaseUnit as QtdBruta,

  // Valor Total Calculado (Linha a Linha)
  cast( Historico.MatlWrhsStkQtyInMatlBaseUnit as abap.fltp ) * cast( Mestre.StandardPrice as abap.fltp ) as ValorTotalCalculado,

  // Preço Unitário
  Mestre.StandardPrice               as PrecoUnitarioBruto

}
where
      Historico.MatlDocLatestPostgDate       > '00000000'
  and Historico.MatlWrhsStkQtyInMatlBaseUnit > 0
