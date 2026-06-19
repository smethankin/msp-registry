export interface OkvedAdditional {
  code: string | null
  name: string | null
  version: string | null
}

export interface License {
  series: string | null
  number: string | null
  lic_type: string | null
  activity_names: string[] | null
  date_issued: string | null
  date_start: string | null
  date_end: string | null
  date_suspended: string | null
  issued_by: string | null
  suspended_by: string | null
}

export interface Product {
  code: string | null
  name: string | null
  is_innovative: boolean | null
}

export interface Partnership {
  partner_inn: string | null
  partner_name: string | null
  contract_date: string | null
  contract_number: string | null
}

export interface EntityDetail {
  id: number
  doc_id: string
  entity_type: 'IP' | 'ORG'
  inn: string
  ogrn: string | null
  full_name: string | null
  short_name: string | null
  date_composed: string | null
  date_included: string | null
  msp_type: number | null
  msp_category: number | null
  is_new: number | null
  social_ent: number | null
  employees_count: number | null
  region_code: string | null
  region_name: string | null
  district_name: string | null
  city_name: string | null
  locality_name: string | null
  okved_main: string | null
  okved_main_name: string | null
  okved_ver: string | null
  okved_list: OkvedAdditional[]
  licenses: License[]
  products: Product[]
  partnerships: Partnership[]
}

export interface EntityCard {
  inn: string
  entity_type: 'IP' | 'ORG'
  full_name: string | null
  ogrn: string | null
  region_name: string | null
  okved_main: string | null
  okved_main_name: string | null
  msp_category: number | null
  date_included: string | null
}

export interface SearchResult {
  total: number
  page: number
  page_size: number
  items: EntityCard[]
}

export interface TaxPayment {
  doc_id: string
  doc_date: string | null
  data_date: string | null
  org_name: string | null
  tax_name: string
  paid_amount: number
}

export interface ImportLog {
  id: number
  type: string
  filename: string
  uploaded_at: string
  records_total: number
  records_inserted: number
  records_updated: number
  status: 'processing' | 'completed' | 'error'
  error_message: string | null
}

export interface Stats {
  total_entities: number
  total_ip: number
  total_org: number
  total_tax_records: number
  last_import: string | null
}
