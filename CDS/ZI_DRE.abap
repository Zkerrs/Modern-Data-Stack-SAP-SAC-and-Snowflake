@AbapCatalog.sqlViewName: 'ZIDREFLOW'
@AbapCatalog.compiler.compareFilter: true
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'Relatório DRE - Demonstração de Resultado'
@Metadata.ignorePropagatedAnnotations: true

@VDM.viewType: #COMPOSITE     
@Analytics.dataCategory: #CUBE 
@OData.publish: true

define view ZI_DRE
  as select from ZI_GLAccountBalanceFlow as Geral
  
  left outer join t077z as TextoGrupo               on  Geral.ChartOfAccounts = TextoGrupo.ktopl
                                                    and Geral.GLAccountGroup  = TextoGrupo.ktoks
                                                    and TextoGrupo.spras      = 'P'
  
  left outer join I_FunctionalAreaText as TextoFunc on  Geral.FunctionalArea = TextoFunc.FunctionalArea
                                                    and TextoFunc.Language   = $session.system_language

  left outer join I_SegmentText as TextoSeg         on  Geral.Segment      = TextoSeg.Segment
                                                    and TextoSeg.Language  = $session.system_language
    
{
  key Geral.CompanyCode,
  key Geral.Ledger,
  key Geral.AccountingDocument                 as DocumentNumber,
  key Geral.LedgerLineItem                     as DocumentItem,
  key Geral.FiscalYear,

  Geral.FiscalPeriod,
  Geral.PostingDate,
  Geral.DocumentDate,

  Geral.ChartOfAccounts,
  Geral.GLAccount,
  Geral.GLAccountName,
  
  Geral.GLAccountType,
  Geral.GLAccountTypeName,
  
  Geral.GLAccountGroup,
  TextoGrupo.txt30             as GLAccountGroupName, 

  Geral.ControllingArea,
  
  Geral.CostCenter,
  Geral.CostCenterName,
  
  Geral.ProfitCenter,
  Geral.ProfitCenterName,
  
  Geral.FunctionalArea,      
  TextoFunc.FunctionalAreaName,
  Geral.Segment,             
  TextoSeg.SegmentName,

  Geral.BusinessArea           as Branch,
  Geral.Plant,
  Geral.PlantName,

  Geral.DocumentType           as DocType,
  Geral.ItemText,
  Geral.RefDocType,

  Geral.Currency,
  Geral.DebitCreditCode,

  // Receita costuma ser negativa (-). 
  @Semantics.amount.currencyCode: 'Currency'
  @DefaultAggregation: #SUM
  Geral.Amount                 as AmountInCompanyCurrency

}
where
      Geral.Ledger = '0L'
