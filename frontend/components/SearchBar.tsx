'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Search } from 'lucide-react'

interface Props {
  initialQuery?: string
  initialType?: string
}

export default function SearchBar({ initialQuery = '', initialType = '' }: Props) {
  const router = useRouter()
  const [query, setQuery] = useState(initialQuery)
  const [type, setType] = useState(initialType)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const q = query.trim()
    if (!q) return
    const params = new URLSearchParams()
    params.set('q', q)
    if (type) params.set('type', type)
    router.push(`/search?${params.toString()}`)
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-3xl mx-auto bg-white rounded-lg shadow-md p-2 flex flex-col sm:flex-row items-stretch gap-2"
    >
      <select
        value={type}
        onChange={e => setType(e.target.value)}
        className="px-4 py-3 border border-gray-200 rounded-md bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
      >
        <option value="">Все</option>
        <option value="IP">ИП</option>
        <option value="ORG">Организации</option>
      </select>
      <div className="flex-1 relative">
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Введите ИНН, ОГРН или наименование"
          className="w-full px-4 py-3 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-base"
        />
      </div>
      <button
        type="submit"
        className="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-md transition-colors flex items-center justify-center gap-2"
      >
        <Search className="w-4 h-4" />
        Найти
      </button>
    </form>
  )
}
