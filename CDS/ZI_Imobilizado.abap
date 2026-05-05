@AbapCatalog.sqlViewName: 'ZIIMOBFL'
@AbapCatalog.compiler.compareFilter: true
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'Relatório Imobilizado'
@Metadata.ignorePropagatedAnnotations: true

@VDM.viewType: #COMPOSITE     
@Analytics.dataCategory: #CUBE 
@OData.publish: true

define view ZI_Imobilizado
  as select from ZI_GLAccountBalanceFlow as Geral

  left outer join I_FixedAsset as _AssetMaster                 on  Geral.CompanyCode      = _AssetMaster.CompanyCode
                                                               and Geral.MasterFixedAsset = _AssetMaster.MasterFixedAsset
                                                               and Geral.FixedAssetSub    = _AssetMaster.FixedAsset
  
  association [0..1] to I_AssetTransactionTypeText as _TrxText on  Geral.AssetTrxType = _TrxText.AssetTransactionType
                                                               and _TrxText.Language  = $session.system_language

  association [0..1] to I_AssetClassText as _ClassText         on  _AssetMaster.AssetClass = _ClassText.AssetClass
                                                               and _ClassText.Language     = $session.system_language

{
  key Geral.CompanyCode,
  key Geral.Ledger,
  key Geral.AccountingDocument,
  key Geral.LedgerLineItem,
  key Geral.FiscalYear,
  
  key Geral.MasterFixedAsset              as AssetMainNumber,
  key Geral.FixedAssetSub                 as AssetSubNumber,
  
  Geral.AssetName,
  _AssetMaster.AssetClass,
  _ClassText.AssetClassDescription,
  
  Geral.AssetTrxType,
  _TrxText.AssetTransactionTypeName,

  Geral.FiscalPeriod,
  Geral.PostingDate,
  Geral.DocumentDate,
  Geral.ReferenceID,       
  Geral.ItemText,          

  Geral.CostCenter,
  Geral.CostCenterName,
  Geral.ProfitCenter,
  Geral.ProfitCenterName,
  Geral.Segment,
  Geral.Plant,
  Geral.PlantName,
  
  -- Capex / Projetos
  Geral.WBSElement,
  Geral.WBSDescription,
  Geral.Project,

  Geral.GLAccount,
  Geral.GLAccountName,
  
  Geral.Supplier,
  Geral.SupplierName,

  Geral.Currency,
  
  @Semantics.amount.currencyCode: 'Currency'
  @DefaultAggregation: #SUM
  Geral.Amount                            as Amount

}
where
    Geral.Ledger = '0L'
    
    
