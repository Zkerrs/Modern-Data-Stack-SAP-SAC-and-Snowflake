@AbapCatalog.sqlViewName: 'ZIGLABLFLOWCB'
@AbapCatalog.compiler.compareFilter: true
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'View Geral Base'
@Metadata.ignorePropagatedAnnotations: true

@VDM.viewType: #COMPOSITE     
@Analytics.dataCategory: #CUBE 
@OData.publish: true

define view ZI_GLAccountBalanceFlow
  as select from    I_GLAccountLineItem          as Item

    left outer join I_GLAccountText              as GLText      on  Item.ChartOfAccounts = GLText.ChartOfAccounts
                                                                and Item.GLAccount       = GLText.GLAccount
                                                                and GLText.Language      = $session.system_language

    left outer join I_GLAccountInChartOfAccounts as MestreConta on  Item.ChartOfAccounts = MestreConta.ChartOfAccounts
                                                                and Item.GLAccount       = MestreConta.GLAccount

    left outer join I_GLAccountGroupText         as TextoGrupo  on  MestreConta.ChartOfAccounts = TextoGrupo.ChartOfAccounts
                                                                and MestreConta.GLAccountGroup  = TextoGrupo.GLAccountGroup
                                                                and TextoGrupo.Language         = $session.system_language

    left outer join I_GLAccountTypeText          as TextoTipo   on  MestreConta.GLAccountType = TextoTipo.GLAccountType
                                                                and TextoTipo.Language        = $session.system_language

    left outer join I_CostCenterText             as CostCenterT on  Item.ControllingArea        =  CostCenterT.ControllingArea
                                                                and Item.CostCenter             =  CostCenterT.CostCenter
                                                                and CostCenterT.Language        = $session.system_language
                                                                and CostCenterT.ValidityEndDate >= '99991231'

    left outer join I_ProfitCenterText           as ProfitCtrT  on  Item.ControllingArea       =  ProfitCtrT.ControllingArea
                                                                and Item.ProfitCenter          =  ProfitCtrT.ProfitCenter
                                                                and ProfitCtrT.Language        = $session.system_language
                                                                and ProfitCtrT.ValidityEndDate >= '99991231'

    left outer join I_Customer                   as Customer    on Item.Customer = Customer.Customer

    left outer join I_Supplier                   as Supplier    on Item.Supplier = Supplier.Supplier

    left outer join I_FixedAsset                 as Asset       on  Item.CompanyCode      = Asset.CompanyCode
                                                                and Item.MasterFixedAsset = Asset.MasterFixedAsset
                                                                and Item.FixedAsset       = Asset.FixedAsset

    left outer join I_ProductText                as MaterialT   on  Item.Product       = MaterialT.Product
                                                                and MaterialT.Language = $session.system_language

    left outer join I_Plant                      as PlantT      on Item.Plant = PlantT.Plant

    left outer join I_WBSElement                 as WBS         on Item.WBSElement = WBS.WBSElement

{
  key Item.CompanyCode                 as CompanyCode,
  key Item.Ledger                      as Ledger,
  key Item.SourceLedger                as SourceLedger,
  key Item.AccountingDocument          as AccountingDocument,
  key Item.LedgerGLLineItem            as LedgerLineItem,
  key Item.FiscalYear                  as FiscalYear,

      Item.OffsettingAccount           as GKONT,
      Item.OffsettingAccountType       as GKOAR,

      Item.FiscalPeriod                as FiscalPeriod,
      Item.ChartOfAccounts             as ChartOfAccounts,
      Item.GLAccount                   as GLAccount,
      GLText.GLAccountName             as GLAccountName,

      MestreConta.GLAccountType,
      TextoTipo.GLAccountTypeName,
      MestreConta.GLAccountGroup,
      TextoGrupo.AccountGroupName,

      Item.FinancialAccountType        as AccountType, -- (Ativo 'A', Material 'M', Fornecedor 'K')

      Item.ControllingArea             as ControllingArea,
      Item.CostCenter                  as CostCenter,
      CostCenterT.CostCenterName       as CostCenterName,
      Item.ProfitCenter                as ProfitCenter,
      ProfitCtrT.ProfitCenterName      as ProfitCenterName,
      Item.FunctionalArea              as FunctionalArea, -- DRE por Função
      Item.BusinessArea                as BusinessArea,
      Item.Segment                     as Segment,

      -- Cliente / Fornecedor
      Item.Customer                    as Customer,
      Customer.CustomerName            as CustomerName,
      Item.Supplier                    as Supplier,
      Supplier.SupplierName            as SupplierName,

      -- Imobilizado---
      Item.MasterFixedAsset            as MasterFixedAsset,
      Item.FixedAsset                  as FixedAssetSub,
      Asset.FixedAssetDescription      as AssetName,
      Item.AssetTransactionType        as AssetTrxType,

      -- Datas (Fluxo de Caixa) ---
      Item.PostingDate                 as PostingDate,  -- Data Lançamento
      Item.DocumentDate                as DocumentDate, -- Data da Nota/Fatura
      Item.NetDueDate                  as NetDueDate,   -- Vencimento Líquido (Previsão de Caixa)
      Item.ClearingDate                as ClearingDate, -- Data da Compensação (Caixa Realizado)
      Item.CreationDate                as CreationDate, -- Auditoria

      -- Documentação ---
      Item.AccountingDocumentType      as DocumentType, -- Tipo Doc (KR, SA, DA)
      Item.DocumentItemText            as ItemText,     -- Histórico
      Item.AssignmentReference         as Assignment,   -- Atribuição (Zuonr)
      Item.ReferenceDocument           as ReferenceID,  -- Nota Fiscal / XBLNR
      Item.ReferenceDocumentType       as RefDocType,
      Item.ClearingJournalEntry        as ClearingDoc,  -- Doc de Pagamento

      -- Logística e Vendas ---
      Item.Product                     as Material,
      MaterialT.ProductName            as MaterialName,
      Item.Plant                       as Plant,
      PlantT.PlantName                 as PlantName,
      Item.SoldProduct                 as SoldProduct,

      -- --- Projetos (CAPEX) ---
      Item.WBSElement                  as WBSElement,
      WBS.WBSElementShortID            as WBSShortID,
      WBS.WBSDescription               as WBSDescription,
      Item.Project                     as Project,

      Item.HouseBank                   as HouseBank,
      Item.HouseBankAccount            as HouseBankAccount,

      -- --- Valor e Quantidade
      Item.DebitCreditCode             as DebitCreditCode, -- S / H

      Item.CompanyCodeCurrency         as Currency,

      @Semantics.amount.currencyCode: 'Currency'
      @DefaultAggregation: #SUM
      Item.AmountInCompanyCodeCurrency as Amount,

      Item.BaseUnit                    as BaseUnit,

      @Semantics.quantity.unitOfMeasure: 'BaseUnit'
      @DefaultAggregation: #SUM
      Item.Quantity                    as Quantity

}

