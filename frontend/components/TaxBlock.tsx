'use client'

import { useEffect, useState } from 'react'
import { getEntityTaxes } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import InfoBlock from '@/components/InfoBlock'
import { DollarSign, Loader2 } from 'lucide-react'
import type { TaxPayment } from '@/types'

export default function TaxBlock({ inn }: { inn: string }) {
  const [taxes, setTaxes] = useState<TaxPayment[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getEntityTaxes(inn)
      .then((data) => {
        if (!cancelled) setTaxes(data)
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [inn])

  if (loading) {
    return (
      <InfoBlock title="Уплаченные налоги" icon={<DollarSign className="w-5 h-5" />}>
        <div className="flex items-center justify-center py-6">
          <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
        </div>
      </InfoBlock>
    )
  }

  if (taxes.length === 0) return null

  const total = taxes.reduce((s, t) => s + t.paid_amount, 0)

  return (
    <InfoBlock title={`Уплаченные налоги (${taxes.length})`} icon={<DollarSign className="w-5 h-5" />}>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-2 pr-4 text-gray-500 font-medium">Налог (сбор, взнос)</th>
              <th className="text-right py-2 pr-4 text-gray-500 font-medium">Сумма, ₽</th>
              <th className="text-left py-2 text-gray-500 font-medium">Дата документа</th>
            </tr>
          </thead>
          <tbody>
            {taxes.map((t, i) => (
              <tr key={i} className="border-b border-gray-50">
                <td className="py-2 pr-4 text-gray-700">{t.tax_name}</td>
                <td className="py-2 pr-4 text-right font-mono tabular-nums text-gray-700">
                  {t.paid_amount.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </td>
                <td className="py-2 text-gray-600 text-sm">{formatDate(t.doc_date) || '—'}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-gray-200 font-semibold">
              <td className="py-2.5 pr-4 text-gray-900">Итого</td>
              <td className="py-2.5 pr-4 text-right font-mono tabular-nums text-gray-900">
                {total.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </td>
              <td className="py-2.5" />
            </tr>
          </tfoot>
        </table>
      </div>
    </InfoBlock>
  )
}
