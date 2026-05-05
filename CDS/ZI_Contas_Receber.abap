@AbapCatalog.sqlViewName: 'ZICNTREC'
@AbapCatalog.compiler.compareFilter: true
@AbapCatalog.preserveKey: true
@AccessControl.authorizationCheck: #NOT_REQUIRED
@EndUserText.label: 'Relatório Contas a Receber'
@Metadata.ignorePropagatedAnnotations: true

@VDM.viewType: #COMPOSITE
@Analytics.dataCategory: #CUBE
@OData.publish: true

define view ZI_Contas_Receber
  as select from I_OperationalAcctgDocItem as bseg

    left outer join t001                                     on bseg.CompanyCode = t001.bukrs
    
  // KNA1: Tabela Mestra de Clientes
    left outer join kna1                                     on bseg.Customer = kna1.kunnr

  // T003T: Texto do Tipo de Documento
    left outer join t003t                                    on  bseg.AccountingDocumentType = t003t.blart
                                                             and t003t.spras                 = $session.system_language

  // J_1BBRANCH: Dados da Filial
    left outer join j_1bbranch                               on  bseg.CompanyCode   = j_1bbranch.bukrs
                                                             and bseg.BusinessPlace = j_1bbranch.branch

    left outer join bseg                      as tabela_bseg on  bseg.CompanyCode            = tabela_bseg.bukrs
                                                             and bseg.AccountingDocument     = tabela_bseg.belnr
                                                             and bseg.FiscalYear             = tabela_bseg.gjahr
                                                             and bseg.AccountingDocumentItem = tabela_bseg.buzei
{
  key bseg.CompanyCode,
  key bseg.AccountingDocument                                  as DocumentNumber,
  key bseg.AccountingDocumentItem                              as DocumentItem,
  key bseg.FiscalYear                                          as FiscalYear,
  key bseg.Customer                                            as Customer,
  key bseg.GLAccount                                           as GLAccount,

      concat( t001.mandt, '' )                                 as MandanteCod,

      bseg.BusinessArea                                        as Branch,
      t001.butxt                                               as CompanyName,
      kna1.name1                                               as CustomerName,
      bseg.AccountingDocumentType                              as DocType,
      bseg.PostingDate                                         as PostingDate,
      bseg.DocumentDate                                        as DocumentDate,
      bseg.NetDueDate                                          as DueDate,
      bseg.FiscalPeriod                                        as FiscalPeriod,

      @Semantics.amount.currencyCode: 'Currency'
      @DefaultAggregation: #SUM
      bseg.AmountInCompanyCodeCurrency                         as AmountLocalCurrency,

      bseg.DebitCreditCode                                     as DebitCredit,

      @Semantics.amount.currencyCode: 'Currency'
      @DefaultAggregation: #SUM
      cast(bseg.AmountInCompanyCodeCurrency as abap.dec(16,2)) as AmountDocumentCurrency,

      @Semantics.currencyCode: true
      bseg.CompanyCodeCurrency                                 as Currency,

      bseg.PostingKey                                          as PostingKey,
      bseg.SpecialGLCode                                       as UMSKZ,
      bseg.SpecialGLTransactionType                            as UMSKS,
      tabela_bseg.zumsk                                        as ZUMSK,
      bseg.DocumentItemText                                    as DocumentText,
      bseg.ClearingJournalEntry                                as ClearingDocument,
      bseg.ClearingDate                                        as ClearingDate,
      
      bseg.ProfitCenter                                        as ProfitCenter,

      bseg.SalesDocument                                       as PedidoVenda,

      bseg.OffsettingAccount                                   as GKONT,
      bseg.OffsettingAccountType                               as GKOAR,

      j_1bbranch.stcd1                                         as CNPJ,
      t003t.ltext                                              as TipoDocumento,
      bseg.InvoiceReference                                    as DocEstorno,

      case
        when bseg.ClearingJournalEntry <> '' then 'Compensado'
        else 'Aberto'
      end                                                      as DocumentStatus,

      @Semantics.amount.currencyCode: 'Currency'
      @DefaultAggregation: #SUM
      case
        when bseg.ClearingJournalEntry is null or bseg.ClearingJournalEntry = ''
        then cast(bseg.AmountInCompanyCodeCurrency as abap.dec(16,2))
        else cast(0 as abap.dec(16,2))
      end                                                      as ValorTotalAberto,

      @Semantics.amount.currencyCode: 'Currency'
      @DefaultAggregation: #SUM
      case
        when bseg.ClearingJournalEntry <> ''
        then cast(bseg.AmountInCompanyCodeCurrency as abap.dec(16,2))
        else cast(0 as abap.dec(16,2))
      end                                                      as ValorTotalCompensado
}
where
      bseg.Customer is not null
  and bseg.Customer <> ''
