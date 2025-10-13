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

export interface UploadResponse {
  success: boolean
  message: string
  dataset_type: string
  original_filename: string
  stored_filename: string
  file_size_mb: number
  statistics: {
    total_new_rows: number
    rows_added: number
    rows_updated: number
    rows_skipped: number
  }
  total_rows: number
  columns: string[]
  storage_info: {
    size: number
    last_modified: string
  }
}

export interface Dataset {
  dataset_type: string
  filename: string
  size: number
  size_mb: number
  last_modified: string
  metadata: Record<string, string>
}

export interface DatasetsResponse {
  success: boolean
  datasets: Dataset[]
  count: number
}

export interface PreviewResponse {
  success: boolean
  dataset_type: string
  total_rows: number
  preview_rows: number
  columns: string[]
  data: Record<string, any>[]
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

  async uploadDataset(file: File, datasetType?: string): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const url = datasetType
      ? `${API_BASE}/upload?dataset_type=${datasetType}`
      : `${API_BASE}/upload`

    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Upload failed')
    }
    return response.json()
  },

  async listDatasets(): Promise<DatasetsResponse> {
    const response = await fetch(`${API_BASE}/datasets`)
    if (!response.ok) throw new Error('Failed to fetch datasets')
    return response.json()
  },

  async previewDataset(datasetType: string, limit = 10): Promise<PreviewResponse> {
    const response = await fetch(`${API_BASE}/datasets/${datasetType}/preview?limit=${limit}`)
    if (!response.ok) throw new Error('Failed to preview dataset')
    return response.json()
  },

  async deleteDataset(datasetType: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE}/datasets/${datasetType}`, {
      method: 'DELETE',
    })
    if (!response.ok) throw new Error('Failed to delete dataset')
    return response.json()
  },
}
