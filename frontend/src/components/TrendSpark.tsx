import React, { useEffect, useState } from 'react'
import { apiClient, TrendItem } from '../api/client'

const TrendSpark: React.FC = () => {
  const [trends, setTrends] = useState<TrendItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchTrends = async () => {
      try {
        const data = await apiClient.getTrends('AE', 24)
        setTrends(data.trends)
      } catch (error) {
        console.error('Failed to fetch trends:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchTrends()
  }, [])

  if (loading) {
    return <div className="animate-pulse bg-gray-200 h-32 rounded"></div>
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Trending Now</h3>
      <div className="space-y-3">
        {trends.map((trend, idx) => (
          <div key={idx} className="flex items-center justify-between">
            <div className="flex-1">
              <span className="text-sm font-medium text-gray-900">
                {trend.color && trend.color} {trend.style && trend.style}
              </span>
            </div>
            <div className="ml-4">
              <div className="flex items-center">
                <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${trend.score * 100}%` }}
                  ></div>
                </div>
                <span className="text-sm text-gray-600">{(trend.score * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default TrendSpark
