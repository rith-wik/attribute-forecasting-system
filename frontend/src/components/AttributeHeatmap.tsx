import React, { useMemo } from 'react'
import { ForecastResult } from '../api/client'

interface AttributeHeatmapProps {
  data: ForecastResult[]
}

const AttributeHeatmap: React.FC<AttributeHeatmapProps> = ({ data }) => {
  // Extract unique colors and sizes from results
  const { heatmapData, colors, sizes } = useMemo(() => {
    if (!data || data.length === 0) {
      return { heatmapData: new Map(), colors: [], sizes: [] }
    }

    const colorSet = new Set<string>()
    const sizeSet = new Set<string>()
    const dataMap = new Map<string, number>()

    // Calculate average forecast for each color-size combination
    data.forEach(result => {
      const { color, size } = result.attributes
      if (color && size) {
        colorSet.add(color)
        sizeSet.add(size)

        const key = `${size}-${color}`
        const avgForecast = result.daily.reduce((sum, d) => sum + d.forecast_units, 0) / result.daily.length

        // Store or update the average
        const existing = dataMap.get(key) || 0
        dataMap.set(key, avgForecast)
      }
    })

    return {
      heatmapData: dataMap,
      colors: Array.from(colorSet).sort(),
      sizes: Array.from(sizeSet).sort((a, b) => {
        // Sort sizes properly (XS, S, M, L, XL, XXL)
        const sizeOrder: Record<string, number> = { 'XS': 1, 'S': 2, 'M': 3, 'L': 4, 'XL': 5, 'XXL': 6 }
        return (sizeOrder[a] || 999) - (sizeOrder[b] || 999)
      })
    }
  }, [data])

  const getColor = (value: number) => {
    if (value >= 5) return 'bg-green-600'
    if (value >= 3) return 'bg-green-500'
    if (value >= 2) return 'bg-yellow-500'
    if (value >= 1) return 'bg-orange-500'
    return 'bg-red-500'
  }

  const getTextColor = (value: number) => {
    return 'text-white'
  }

  if (data.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Attribute Forecast Heatmap</h3>
        <div className="text-center py-12 text-gray-500">
          <p>No forecast data available</p>
          <p className="text-sm mt-2">Run a prediction to see the heatmap</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">Attribute Forecast Heatmap (Avg Units/Day)</h3>
        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center">
            <div className="w-4 h-4 bg-green-600 rounded mr-1"></div>
            <span>High (5+)</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-yellow-500 rounded mr-1"></div>
            <span>Medium (2-5)</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-red-500 rounded mr-1"></div>
            <span>Low (&lt;2)</span>
          </div>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead>
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase sticky left-0 bg-white">
                Size
              </th>
              {colors.map(color => (
                <th key={color} className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                  {color}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {sizes.map(size => (
              <tr key={size} className="hover:bg-gray-50">
                <td className="px-3 py-2 text-sm font-medium text-gray-900 sticky left-0 bg-white">
                  {size}
                </td>
                {colors.map(color => {
                  const key = `${size}-${color}`
                  const value = heatmapData.get(key) || 0
                  return (
                    <td key={key} className="px-3 py-2 text-center">
                      {value > 0 ? (
                        <div
                          className={`inline-block px-2 py-1 rounded ${getColor(value)} ${getTextColor(value)} text-sm font-medium cursor-pointer hover:opacity-80 transition`}
                          title={`${size} ${color}: ${value.toFixed(2)} units/day`}
                        >
                          {value.toFixed(1)}
                        </div>
                      ) : (
                        <div className="text-gray-300 text-sm">-</div>
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default AttributeHeatmap
