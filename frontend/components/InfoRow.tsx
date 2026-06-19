import { cn } from '@/lib/utils'

interface Props {
  label: string
  value: string | null | undefined
  className?: string
}

export default function InfoRow({ label, value, className }: Props) {
  return (
    <div
      className={cn(
        'grid grid-cols-1 sm:grid-cols-3 gap-1 sm:gap-4 py-2 border-b border-gray-100 last:border-b-0',
        className
      )}
    >
      <dt className="text-sm text-gray-500 sm:col-span-1">{label}</dt>
      <dd className="text-sm font-medium text-gray-900 sm:col-span-2">
        {value || '—'}
      </dd>
    </div>
  )
}
