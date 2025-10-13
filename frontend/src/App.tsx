import React from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import SKUDetail from './pages/SKUDetail'
import DataManagement from './pages/DataManagement'

function Navigation() {
  const location = useLocation()

  const isActive = (path: string) => location.pathname === path

  return (
    <header className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Attribute Forecasting System
          </h1>
          <nav className="flex space-x-8">
            <Link
              to="/"
              className={`px-3 py-2 rounded-md text-sm font-medium ${
                isActive('/')
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              Dashboard
            </Link>
            <Link
              to="/data"
              className={`px-3 py-2 rounded-md text-sm font-medium ${
                isActive('/data')
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              Data Management
            </Link>
          </nav>
        </div>
      </div>
    </header>
  )
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/data" element={<DataManagement />} />
            <Route path="/sku/:sku" element={<SKUDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
