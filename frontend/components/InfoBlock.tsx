interface Props {
  title: string
  children: React.ReactNode
  icon?: React.ReactNode
}

export default function InfoBlock({ title, children, icon }: Props) {
  return (
    <section className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3 bg-gray-50">
        {icon && <div className="text-primary-600">{icon}</div>}
        <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
      </div>
      <div className="p-6">{children}</div>
    </section>
  )
}
