import React, { useState } from 'react'
import { WhatIf } from '../api/client'

interface WhatIfPanelProps {
  onApply: (whatIf: WhatIf) => void
}

const WhatIfPanel: React.FC<WhatIfPanelProps> = ({ onApply }) => {
  const [priceDelta, setPriceDelta] = useState<number>(0)
  const [promoFlag, setPromoFlag] = useState<number>(0)
  const [trendColor, setTrendColor] = useState<string>('Black')
  const [trendBoost, setTrendBoost] = useState<number>(0)

  const handleApply = () => {
    const whatIf: WhatIf = {
      price_delta: priceDelta !== 0 ? priceDelta : undefined,
      promo_flag: promoFlag,
      trend_boost: trendBoost !== 0 ? { [trendColor]: trendBoost } : undefined,
    }
    onApply(whatIf)
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">What-If Analysis</h3>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Price Change ($)</label>
          <input
            type="number"
            step="0.5"
            value={priceDelta}
            onChange={(e) => setPriceDelta(parseFloat(e.target.value))}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2 border"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Promotion</label>
          <select
            value={promoFlag}
            onChange={(e) => setPromoFlag(parseInt(e.target.value))}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2 border"
          >
            <option value={0}>No Promo</option>
            <option value={1}>Active Promo</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Trend Boost Color</label>
          <select
            value={trendColor}
            onChange={(e) => setTrendColor(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2 border"
          >
            <option value="Black">Black</option>
            <option value="White">White</option>
            <option value="Flame">Flame</option>
            <option value="Navy">Navy</option>
            <option value="Olive">Olive</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Trend Boost Amount</label>
          <input
            type="number"
            step="0.1"
            min="0"
            max="1"
            value={trendBoost}
            onChange={(e) => setTrendBoost(parseFloat(e.target.value))}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2 border"
          />
        </div>

        <button
          onClick={handleApply}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition duration-150"
        >
          Apply Scenario
        </button>
      </div>
    </div>
  )
}

export default WhatIfPanel
