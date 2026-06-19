import axios from 'axios'
import type { EntityDetail, SearchResult, ImportLog, Stats, TaxPayment } from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: API_URL })

export async function searchEntities(
  q: string,
  type?: string,
  page = 1,
  pageSize = 20
): Promise<SearchResult> {
  const params: Record<string, any> = { q, page, page_size: pageSize }
  if (type) params.type = type
  const { data } = await api.get('/api/search', { params })
  return data
}

export async function getEntity(inn: string): Promise<EntityDetail> {
  const { data } = await api.get(`/api/entity/${inn}`)
  return data
}

export async function getEntityTaxes(inn: string): Promise<TaxPayment[]> {
  const { data } = await api.get(`/api/entity/${inn}/taxes`)
  return data
}

export async function uploadXml(file: File, onProgress?: (pct: number) => void): Promise<{ import_id: number }> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/api/admin/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: e => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded * 100) / e.total))
    }
  })
  return data
}

export async function getImports(): Promise<ImportLog[]> {
  const { data } = await api.get('/api/admin/imports')
  return data
}

export async function getImportStatus(id: number): Promise<ImportLog> {
  const { data } = await api.get(`/api/admin/imports/${id}`)
  return data
}

export async function getStats(): Promise<Stats> {
  const { data } = await api.get('/api/stats')
  return data
}
