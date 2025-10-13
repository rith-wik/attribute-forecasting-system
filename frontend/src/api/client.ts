const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1'

export interface WhatIf {
  price_delta?: number
  promo_flag?: number
  trend_boost?: Record<string, number>
}

export interface PredictRequest {
  horizon_days: number
  store_ids?: string[]
  skus?: string[]
  level: string
  what_if?: WhatIf
}

export interface DailyForecast {
  date: string
  forecast_units: number
  lo: number
  hi: number
}

export interface ForecastResult {
  store_id: string
  sku: string
  attributes: Record<string, string>
  daily: DailyForecast[]
  explain: Record<string, number>
}

export interface PredictResponse {
  generated_at: string
  horizon_days: number
  results: ForecastResult[]
}

export interface TrainRequest {
  backfill_days: number
  retrain: boolean
}

export interface TrainResponse {
  status: string
  version: string
}

export interface TrendItem {
  color?: string
  style?: string
  score: number
}

export interface TrendsResponse {
  region: string
  window_hours: number
  trends: TrendItem[]
}

export const apiClient = {
  async predict(req: PredictRequest): Promise<PredictResponse> {
    const response = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    })
    if (!response.ok) throw new Error('Prediction failed')
    return response.json()
  },

  async train(req: TrainRequest): Promise<TrainResponse> {
    const response = await fetch(`${API_BASE}/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    })
    if (!response.ok) throw new Error('Training failed')
    return response.json()
  },

  async getTrends(region?: string, windowHours = 24): Promise<TrendsResponse> {
    const params = new URLSearchParams()
    if (region) params.append('region', region)
    params.append('window_hours', windowHours.toString())

    const response = await fetch(`${API_BASE}/trends?${params}`)
    if (!response.ok) throw new Error('Failed to fetch trends')
    return response.json()
  },

  async uploadFiles(files: File[]): Promise<{ status: string; files_received: string[] }> {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))

    const response = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    })
    if (!response.ok) throw new Error('Upload failed')
    return response.json()
  },
}
