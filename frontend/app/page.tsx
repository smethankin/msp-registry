import { getStats } from '@/lib/api'
import SearchBar from '@/components/SearchBar'
import Header from '@/components/Header'
import { Building2, Users, TrendingUp } from 'lucide-react'

async function fetchStats() {
  try {
    return await getStats()
  } catch {
    return null
  }
}

export default async function HomePage() {
  const stats = await fetchStats()

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <Header />
      <main className="container mx-auto px-4">
        {/* Hero */}
        <div className="flex flex-col items-center justify-center pt-20 pb-12 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-3">
            Реестр субъектов МСП
          </h1>
          <p className="text-lg text-gray-500 mb-10 max-w-xl">
            Поиск индивидуальных предпринимателей и организаций по данным ФНС России
          </p>
          <div className="w-full max-w-2xl">
            <SearchBar />
          </div>
          <p className="mt-4 text-sm text-gray-400">
            Поиск по ФИО, ИНН, ОГРН или названию организации
          </p>
        </div>

        {/* Статистика */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto pb-20">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center gap-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <TrendingUp className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {stats.total_entities.toLocaleString('ru-RU')}
                </div>
                <div className="text-sm text-gray-500">Всего записей</div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center gap-4">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <Users className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {stats.total_ip.toLocaleString('ru-RU')}
                </div>
                <div className="text-sm text-gray-500">Индивидуальных предпринимателей</div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center gap-4">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <Building2 className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {stats.total_org.toLocaleString('ru-RU')}
                </div>
                <div className="text-sm text-gray-500">Организаций</div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
