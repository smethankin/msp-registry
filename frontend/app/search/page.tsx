'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { searchEntities } from '@/lib/api'
import type { SearchResult } from '@/types'
import Header from '@/components/Header'
import SearchBar from '@/components/SearchBar'
import EntityCard from '@/components/EntityCard'
import { ChevronLeft, ChevronRight, Loader2 } from 'lucide-react'

function SearchContent() {
  const searchParams = useSearchParams()
  const router = useRouter()

  const q = searchParams.get('q') || ''
  const type = searchParams.get('type') || ''
  const page = parseInt(searchParams.get('page') || '1', 10)

  const [result, setResult] = useState<SearchResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!q) return
    setLoading(true)
    setError(null)
    searchEntities(q, type || undefined, page)
      .then(setResult)
      .catch(() => setError('Ошибка при выполнении поиска. Проверьте подключение к серверу.'))
      .finally(() => setLoading(false))
  }, [q, type, page])

  const totalPages = result ? Math.ceil(result.total / result.page_size) : 0

  const goPage = (p: number) => {
    const params = new URLSearchParams()
    params.set('q', q)
    if (type) params.set('type', type)
    params.set('page', String(p))
    router.push(`/search?${params.toString()}`)
  }

  return (
    <main className="container mx-auto px-4 py-8 max-w-4xl">
      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-blue-600 animate-spin mr-3" />
          <span className="text-gray-600">Поиск...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {!loading && result && (
        <>
          <div className="mb-4 text-sm text-gray-500">
            {result.total === 0
              ? `Ничего не найдено по запросу «${q}»`
              : `Найдено: ${result.total.toLocaleString('ru-RU')} записей`}
          </div>

          <div className="space-y-3">
            {result.items.map((item) => (
              <EntityCard key={item.inn} entity={item} />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3 mt-8">
              <button
                onClick={() => goPage(page - 1)}
                disabled={page <= 1}
                className="flex items-center gap-1 px-4 py-2 rounded-lg border border-gray-300 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
                Предыдущая
              </button>
              <span className="text-sm text-gray-600">
                Страница {page} из {totalPages}
              </span>
              <button
                onClick={() => goPage(page + 1)}
                disabled={page >= totalPages}
                className="flex items-center gap-1 px-4 py-2 rounded-lg border border-gray-300 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Следующая
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </>
      )}
    </main>
  )
}

export default function SearchPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="bg-white border-b border-gray-200 py-4">
        <div className="container mx-auto px-4">
          <SearchBar />
        </div>
      </div>
      <Suspense fallback={<div className="container mx-auto px-4 py-8 max-w-4xl text-center text-gray-600">Загрузка...</div>}>
        <SearchContent />
      </Suspense>
    </div>
  )
}
