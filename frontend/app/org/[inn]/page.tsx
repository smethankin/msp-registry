'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { getEntity } from '@/lib/api'
import Header from '@/components/Header'
import InfoBlock from '@/components/InfoBlock'
import InfoRow from '@/components/InfoRow'
import { formatDate, getMspCategoryLabel } from '@/lib/utils'
import { Building2, MapPin, Briefcase, Award, Package, Handshake, Loader2 } from 'lucide-react'
import type { EntityDetail } from '@/types'

export default function OrgPage() {
  const params = useParams()
  const router = useRouter()
  const inn = params.inn as string

  const [entity, setEntity] = useState<EntityDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!inn) return

    const fetchEntity = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await getEntity(inn)
        
        if (data.entity_type !== 'ORG') {
          setError('Запись не найдена')
          return
        }
        
        setEntity(data)
      } catch (err) {
        setError('Запись не найдена')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchEntity()
  }, [inn])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="container mx-auto px-4 py-8 flex items-center justify-center h-96">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
            <span className="text-gray-600">Загрузка...</span>
          </div>
        </main>
      </div>
    )
  }

  if (error || !entity) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="container mx-auto px-4 py-8 max-w-4xl">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-700 font-medium mb-2">Запись не найдена</p>
            <p className="text-red-600 text-sm mb-4">Субъект МСП с указанным ИНН не существует в реестре.</p>
            <button
              onClick={() => router.back()}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Вернуться назад
            </button>
          </div>
        </main>
      </div>
    )
  }

  const mspCatColors: Record<number, string> = {
    1: 'bg-sky-100 text-sky-700',
    2: 'bg-emerald-100 text-emerald-700',
    3: 'bg-violet-100 text-violet-700',
  }
  const catColor = entity.msp_category ? mspCatColors[entity.msp_category] : 'bg-gray-100 text-gray-600'

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Шапка */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
              <Building2 className="w-7 h-7 text-purple-600" />
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl font-bold text-gray-900 mb-1 break-words">
                {entity.full_name || 'Наименование не указано'}
              </h1>
              {entity.short_name && entity.short_name !== entity.full_name && (
                <p className="text-gray-500 text-sm mb-2">{entity.short_name}</p>
              )}
              <div className="flex flex-wrap gap-2 mb-3">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                  Организация
                </span>
                {entity.msp_category && (
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${catColor}`}>
                    {getMspCategoryLabel(entity.msp_category)}
                  </span>
                )}
                {entity.social_ent === 1 && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-pink-100 text-pink-700">
                    Социальное предприятие
                  </span>
                )}
              </div>
              {entity.ogrn && (
                <p className="text-sm text-gray-500">ОГРН: <span className="font-mono text-gray-700">{entity.ogrn}</span></p>
              )}
            </div>
          </div>
        </div>

        {/* Основные сведения */}
        <InfoBlock title="Основные сведения" icon={<Briefcase className="w-5 h-5" />}>
          <InfoRow label="ИНН" value={entity.inn} />
          <InfoRow label="ОГРН" value={entity.ogrn} />
          <InfoRow label="Дата включения в реестр МСП" value={formatDate(entity.date_included)} />
          <InfoRow label="Категория субъекта МСП" value={getMspCategoryLabel(entity.msp_category)} />
          <InfoRow label="Среднесписочная численность работников" value={entity.employees_count != null ? String(entity.employees_count) : null} />
          <InfoRow label="Социальное предприятие" value={entity.social_ent === 1 ? 'Да' : 'Нет'} />
        </InfoBlock>

        {/* Место нахождения */}
        <InfoBlock title="Место нахождения" icon={<MapPin className="w-5 h-5" />}>
          <InfoRow label="Регион" value={entity.region_name ? `${entity.region_name}${entity.region_code ? ` (${entity.region_code})` : ''}` : entity.region_code} />
          <InfoRow label="Район" value={entity.district_name} />
          <InfoRow label="Город" value={entity.city_name} />
          <InfoRow label="Населённый пункт" value={entity.locality_name} />
        </InfoBlock>

        {/* Основной ОКВЭД */}
        <InfoBlock title="Основной вид деятельности (ОКВЭД)" icon={<Award className="w-5 h-5" />}>
          <InfoRow label="Код ОКВЭД" value={entity.okved_main} />
          <InfoRow label="Наименование" value={entity.okved_main_name} />
          <InfoRow label="Версия справочника" value={entity.okved_ver} />
        </InfoBlock>

        {/* Дополнительные ОКВЭД */}
        {entity.okved_list && entity.okved_list.length > 0 && (
          <InfoBlock title={`Дополнительные виды деятельности (${entity.okved_list.length})`} icon={<Award className="w-5 h-5" />}>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left py-2 pr-4 text-gray-500 font-medium w-28">Код</th>
                    <th className="text-left py-2 text-gray-500 font-medium">Наименование</th>
                  </tr>
                </thead>
                <tbody>
                  {entity.okved_list.map((ok, i) => (
                    <tr key={i} className="border-b border-gray-50">
                      <td className="py-2 pr-4 font-mono text-gray-700">{ok.code || '—'}</td>
                      <td className="py-2 text-gray-700">{ok.name || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </InfoBlock>
        )}

        {/* Лицензии */}
        {entity.licenses && entity.licenses.length > 0 && (
          <InfoBlock title={`Лицензии (${entity.licenses.length})`} icon={<Award className="w-5 h-5" />}>
            <div className="space-y-4">
              {entity.licenses.map((lic, i) => (
                <div key={i} className="border border-gray-100 rounded-lg p-4">
                  <div className="font-medium text-gray-800 mb-2">
                    {[lic.series, lic.number].filter(Boolean).join(' № ') || 'Лицензия'}
                    {lic.lic_type && <span className="ml-2 text-sm text-gray-500">({lic.lic_type})</span>}
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1 text-sm">
                    <InfoRow label="Дата выдачи" value={formatDate(lic.date_issued)} />
                    <InfoRow label="Начало действия" value={formatDate(lic.date_start)} />
                    <InfoRow label="Окончание действия" value={formatDate(lic.date_end)} />
                    {lic.date_suspended && <InfoRow label="Приостановлена" value={formatDate(lic.date_suspended)} />}
                  </div>
                  <InfoRow label="Выдана" value={lic.issued_by} />
                  {lic.activity_names && lic.activity_names.length > 0 && (
                    <div className="mt-2">
                      <span className="text-xs text-gray-500">Виды деятельности по лицензии:</span>
                      <ul className="mt-1 text-sm text-gray-700 list-disc list-inside">
                        {lic.activity_names.map((name, j) => <li key={j}>{name}</li>)}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </InfoBlock>
        )}

        {/* Продукция */}
        {entity.products && entity.products.length > 0 && (
          <InfoBlock title={`Производимая продукция (${entity.products.length})`} icon={<Package className="w-5 h-5" />}>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left py-2 pr-4 text-gray-500 font-medium w-36">Код</th>
                    <th className="text-left py-2 text-gray-500 font-medium">Наименование</th>
                    <th className="text-left py-2 pl-4 text-gray-500 font-medium w-32">Инновационная</th>
                  </tr>
                </thead>
                <tbody>
                  {entity.products.map((p, i) => (
                    <tr key={i} className="border-b border-gray-50">
                      <td className="py-2 pr-4 font-mono text-gray-700">{p.code || '—'}</td>
                      <td className="py-2 text-gray-700">{p.name || '—'}</td>
                      <td className="py-2 pl-4 text-gray-700">{p.is_innovative ? 'Да' : 'Нет'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </InfoBlock>
        )}

        {/* Партнёрство */}
        {entity.partnerships && entity.partnerships.length > 0 && (
          <InfoBlock title={`Программы партнёрства (${entity.partnerships.length})`} icon={<Handshake className="w-5 h-5" />}>
            <div className="space-y-3">
              {entity.partnerships.map((pp, i) => (
                <div key={i} className="border border-gray-100 rounded-lg p-4 text-sm">
                  <InfoRow label="ИНН партнёра" value={pp.partner_inn} />
                  <InfoRow label="Наименование" value={pp.partner_name} />
                  <InfoRow label="Дата договора" value={formatDate(pp.contract_date)} />
                  <InfoRow label="Номер договора" value={pp.contract_number} />
                </div>
              ))}
            </div>
          </InfoBlock>
        )}
      </main>
    </div>
  )
}
