import Link from 'next/link'
import { Building2, User } from 'lucide-react'
import type { EntityCard as EntityCardType } from '@/types'
import { formatDate, getMspCategoryLabel } from '@/lib/utils'

interface Props {
  entity: EntityCardType
}

export default function EntityCard({ entity }: Props) {
  const isIp = entity.entity_type === 'IP'
  const href = isIp ? `/ip/${entity.inn}` : `/org/${entity.inn}`

  return (
    <Link
      href={href}
      className="block bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md hover:border-primary-500 transition-all p-5 group"
    >
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-12 h-12 bg-primary-50 rounded-lg flex items-center justify-center">
          {isIp ? (
            <User className="w-6 h-6 text-primary-600" />
          ) : (
            <Building2 className="w-6 h-6 text-primary-600" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <h3 className="text-lg font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
              {entity.full_name || '—'}
            </h3>
            <span
              className={`flex-shrink-0 px-2 py-1 text-xs font-semibold rounded ${
                isIp ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'
              }`}
            >
              {isIp ? 'ИП' : 'ЮЛ'}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1 text-sm text-gray-600">
            <div>
              <span className="text-gray-500">ИНН:</span>{' '}
              <span className="font-medium text-gray-800">{entity.inn}</span>
            </div>
            {entity.ogrn && (
              <div>
                <span className="text-gray-500">{isIp ? 'ОГРНИП' : 'ОГРН'}:</span>{' '}
                <span className="font-medium text-gray-800">{entity.ogrn}</span>
              </div>
            )}
            {entity.region_name && (
              <div>
                <span className="text-gray-500">Регион:</span>{' '}
                <span className="font-medium text-gray-800">{entity.region_name}</span>
              </div>
            )}
            {entity.msp_category != null && (
              <div>
                <span className="text-gray-500">Категория:</span>{' '}
                <span className="font-medium text-green-700">
                  {getMspCategoryLabel(entity.msp_category)}
                </span>
              </div>
            )}
            {(entity.okved_main || entity.okved_main_name) && (
              <div className="sm:col-span-2">
                <span className="text-gray-500">ОКВЭД:</span>{' '}
                <span className="font-medium text-gray-800">
                  {entity.okved_main}
                  {entity.okved_main_name ? ` — ${entity.okved_main_name}` : ''}
                </span>
              </div>
            )}
            {entity.date_included && (
              <div>
                <span className="text-gray-500">В реестре с:</span>{' '}
                <span className="font-medium text-gray-800">
                  {formatDate(entity.date_included)}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </Link>
  )
}
