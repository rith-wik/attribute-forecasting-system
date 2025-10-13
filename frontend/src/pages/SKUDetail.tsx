import React, { useEffect, useState, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { apiClient, ForecastResult } from '../api/client'
import Plot from 'react-plotly.js'

const SKUDetail: React.FC = () => {
  const { sku } = useParams<{ sku: string }>()
  const [forecast, setForecast] = useState<ForecastResult | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchSKUForecast = async () => {
      try {
        const data = await apiClient.predict({
          horizon_days: 30,
          skus: [sku!],
          level: 'attribute',
        })
        if (data.results.length > 0) {
          setForecast(data.results[0])
        }
      } catch (error) {
        console.error('Failed to fetch SKU forecast:', error)
      } finally {
        setLoading(false)
      }
    }

    if (sku) {
      fetchSKUForecast()
    }
  }, [sku])

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!forecast || !forecast.daily) return null

    const dates = forecast.daily.map(d => d.date)
    const forecasts = forecast.daily.map(d => d.forecast_units)
    const los = forecast.daily.map(d => d.lo)
    const his = forecast.daily.map(d => d.hi)

    return { dates, forecasts, los, his }
  }, [forecast])

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="animate-pulse bg-gray-200 h-64 rounded"></div>
      </div>
    )
  }

  if (!forecast) {
    return (
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg p-6">
          <p className="text-gray-500">No forecast data available for this SKU</p>
          <Link to="/" className="text-blue-600 hover:text-blue-900 mt-4 inline-block">
            Back to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div className="mb-4">
        <Link to="/" className="text-blue-600 hover:text-blue-900">
          ← Back to Dashboard
        </Link>
      </div>

      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">SKU: {sku}</h2>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-500">Color</p>
            <p className="text-lg font-medium">{forecast.attributes.color}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Size</p>
            <p className="text-lg font-medium">{forecast.attributes.size}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Style</p>
            <p className="text-lg font-medium">{forecast.attributes.style}</p>
          </div>
        </div>
      </div>

      {/* Forecast Chart */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">30-Day Forecast</h3>
        {chartData && (
          <Plot
            data={[
              {
                x: chartData.dates,
                y: chartData.his,
                type: 'scatter',
                mode: 'lines',
                name: 'Upper Bound',
                line: { color: 'rgba(59, 130, 246, 0.3)', width: 0 },
                fillcolor: 'rgba(59, 130, 246, 0.1)',
                fill: 'tonexty',
                showlegend: false,
              },
              {
                x: chartData.dates,
                y: chartData.los,
                type: 'scatter',
                mode: 'lines',
                name: 'Lower Bound',
                line: { color: 'rgba(59, 130, 246, 0.3)', width: 0 },
                fillcolor: 'rgba(59, 130, 246, 0.1)',
                fill: 'tozeroy',
                showlegend: false,
              },
              {
                x: chartData.dates,
                y: chartData.forecasts,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Forecast',
                line: { color: 'rgb(59, 130, 246)', width: 2 },
                marker: { size: 6 },
              },
            ]}
            layout={{
              autosize: true,
              xaxis: { title: 'Date' },
              yaxis: { title: 'Units', rangemode: 'tozero' },
              hovermode: 'x unified',
              showlegend: true,
              margin: { l: 50, r: 20, t: 20, b: 50 },
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%', height: '400px' }}
          />
        )}
      </div>

      {/* Forecast Table */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Daily Forecast Data</h3>
        <div className="overflow-x-auto max-h-96">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="sticky top-0 bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Forecast</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Low</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">High</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Range</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {forecast.daily.map((day, idx) => {
                const range = day.hi - day.lo
                return (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{day.date}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 text-right">
                      {day.forecast_units.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {day.lo.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {day.hi.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                      ±{(range / 2).toFixed(2)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Explainability */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Feature Contributions</h3>
        <div className="space-y-3">
          {Object.entries(forecast.explain).map(([feature, contribution]) => (
            <div key={feature}>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">{feature}</span>
                <span className="text-sm text-gray-600">{(contribution * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${contribution > 0 ? 'bg-green-600' : 'bg-red-600'}`}
                  style={{ width: `${Math.abs(contribution) * 100}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default SKUDetail
