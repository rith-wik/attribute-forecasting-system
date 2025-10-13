import React from 'react'

interface KPIProps {
  title: string
  value: string | number
  subtitle?: string
}

const KPI: React.FC<KPIProps> = ({ title, value, subtitle }) => {
  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-1">
            <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">{value}</dd>
            {subtitle && <dd className="mt-1 text-sm text-gray-600">{subtitle}</dd>}
          </div>
        </div>
      </div>
    </div>
  )
}

export default KPI
