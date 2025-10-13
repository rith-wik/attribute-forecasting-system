import React, { useState, useEffect, useRef } from 'react'
import { apiClient, Dataset, UploadResponse, PreviewResponse } from '../api/client'

const DataManagement: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [preview, setPreview] = useState<PreviewResponse | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    fetchDatasets()
  }, [])

  const fetchDatasets = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiClient.listDatasets()
      setDatasets(response.datasets)
    } catch (err) {
      setError('Failed to load datasets')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFileUpload(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await handleFileUpload(e.target.files[0])
    }
  }

  const handleFileUpload = async (file: File) => {
    const validExtensions = ['.csv', '.xlsx']
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()

    if (!validExtensions.includes(fileExt)) {
      setError(`Invalid file type. Please upload ${validExtensions.join(' or ')} files.`)
      return
    }

    setUploading(true)
    setError(null)
    setUploadResult(null)

    try {
      const result = await apiClient.uploadDataset(file)
      setUploadResult(result)
      await fetchDatasets() // Refresh the list
    } catch (err: any) {
      setError(err.message || 'Upload failed')
      console.error(err)
    } finally {
      setUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handlePreview = async (datasetType: string) => {
    try {
      const result = await apiClient.previewDataset(datasetType, 10)
      setPreview(result)
    } catch (err) {
      setError('Failed to preview dataset')
      console.error(err)
    }
  }

  const handleDelete = async (datasetType: string) => {
    if (!confirm(`Are you sure you want to delete the ${datasetType} dataset?`)) {
      return
    }

    try {
      await apiClient.deleteDataset(datasetType)
      await fetchDatasets()
      setPreview(null)
    } catch (err) {
      setError('Failed to delete dataset')
      console.error(err)
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString()
  }

  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div className="px-4 py-6 sm:px-0">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Data Management</h1>

        {/* Upload Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Upload Dataset</h2>

          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center ${
              dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <div className="flex flex-col items-center">
                <svg
                  className="w-12 h-12 text-gray-400 mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
                <p className="text-lg font-medium text-gray-700">
                  Drop your file here or click to browse
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  Supported formats: CSV, XLSX (Max 50MB)
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Filename should contain: products, sales, or inventory
                </p>
              </div>
            </label>
          </div>

          {uploading && (
            <div className="mt-4 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="text-gray-600 mt-2">Uploading and processing...</p>
            </div>
          )}

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {uploadResult && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded">
              <h3 className="font-semibold text-green-900 mb-2">Upload Successful!</h3>
              <div className="text-sm text-green-800 space-y-1">
                <p>Dataset Type: <strong>{uploadResult.dataset_type}</strong></p>
                <p>File: {uploadResult.original_filename} ({uploadResult.file_size_mb} MB)</p>
                <p>Total Rows: <strong>{uploadResult.total_rows}</strong></p>
                <p>
                  Statistics: {uploadResult.statistics.rows_added} added,
                  {' '}{uploadResult.statistics.rows_updated} updated,
                  {' '}{uploadResult.statistics.rows_skipped} skipped
                </p>
                <p className="text-xs mt-2 text-gray-600">
                  Columns: {uploadResult.columns.join(', ')}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Datasets List */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Datasets</h2>
            <button
              onClick={fetchDatasets}
              className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
              disabled={loading}
            >
              Refresh
            </button>
          </div>

          {loading && !datasets.length ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : datasets.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              No datasets uploaded yet. Upload your first dataset above.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Size
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Modified
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {datasets.map((dataset) => (
                    <tr key={dataset.dataset_type}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                          {dataset.dataset_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {dataset.size_mb} MB
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(dataset.last_modified)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button
                          onClick={() => handlePreview(dataset.dataset_type)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Preview
                        </button>
                        <button
                          onClick={() => handleDelete(dataset.dataset_type)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Preview Modal */}
        {preview && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-6xl shadow-lg rounded-md bg-white">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">
                  Preview: {preview.dataset_type} ({preview.total_rows} total rows)
                </h3>
                <button
                  onClick={() => setPreview(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {preview.columns.map((col) => (
                        <th
                          key={col}
                          className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {preview.data.map((row, idx) => (
                      <tr key={idx}>
                        {preview.columns.map((col) => (
                          <td key={col} className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                            {String(row[col])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-4 text-sm text-gray-500">
                Showing {preview.preview_rows} of {preview.total_rows} rows
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default DataManagement
