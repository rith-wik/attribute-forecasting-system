import React, { useState, useEffect } from 'react'
import { apiClient, PredictRequest, ForecastResult, WhatIf } from '../api/client'
import KPI from '../components/KPI'
import TrendSpark from '../components/TrendSpark'
import AttributeHeatmap from '../components/AttributeHeatmap'
import ForecastTable from '../components/ForecastTable'
import WhatIfPanel from '../components/WhatIfPanel'

const Dashboard: React.FC = () => {
  const [results, setResults] = useState<ForecastResult[]>([])
  const [loading, setLoading] = useState(false)

  const fetchForecasts = async (whatIf?: WhatIf) => {
    setLoading(true)
    try {
      const request: PredictRequest = {
        horizon_days: 7,
        store_ids: ['DXB01', 'DXB02'],
        skus: ['A1001', 'A1002'],
        level: 'attribute',
        what_if: whatIf,
      }
      const data = await apiClient.predict(request)
      setResults(data.results)
    } catch (error) {
      console.error('Failed to fetch forecasts:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchForecasts()
  }, [])

  const handleWhatIf = (whatIf: WhatIf) => {
    fetchForecasts(whatIf)
  }

  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      {/* KPIs */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3 mb-6">
        <KPI title="Avg MAPE" value="24.5%" subtitle="Target: ≤30%" />
        <KPI title="Top Rising Color" value="Flame" subtitle="+18% vs last week" />
        <KPI title="Stockout Risk" value="3" subtitle="SKUs need attention" />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Column - Charts */}
        <div className="lg:col-span-2 space-y-6">
          {loading ? (
            <div className="animate-pulse bg-gray-200 h-64 rounded"></div>
          ) : (
            <>
              <AttributeHeatmap data={results} />
              <ForecastTable results={results} />
            </>
          )}
        </div>

        {/* Right Column - Controls */}
        <div className="space-y-6">
          <TrendSpark />
          <WhatIfPanel onApply={handleWhatIf} />
        </div>
      </div>
    </div>
  )
}

export default Dashboard
