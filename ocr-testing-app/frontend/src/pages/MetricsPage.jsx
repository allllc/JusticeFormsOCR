import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { metricsAPI, testsAPI } from '../services/api'

function MetricsPage() {
  const [selectedTestRuns, setSelectedTestRuns] = useState([])

  // Fetch aggregate metrics
  const { data: aggregateData, isLoading: aggregateLoading } = useQuery({
    queryKey: ['metrics-aggregate'],
    queryFn: () => metricsAPI.getAggregate(),
  })

  // Fetch field metrics
  const { data: fieldData, isLoading: fieldLoading } = useQuery({
    queryKey: ['metrics-by-field'],
    queryFn: () => metricsAPI.getByField(),
  })

  // Fetch test runs for comparison
  const { data: testsData } = useQuery({
    queryKey: ['tests'],
    queryFn: () => testsAPI.list(),
  })

  // Fetch comparison data
  const { data: comparisonData } = useQuery({
    queryKey: ['metrics-comparison', selectedTestRuns],
    queryFn: () => metricsAPI.getComparison(selectedTestRuns),
    enabled: selectedTestRuns.length >= 2,
  })

  const handleExport = async (format) => {
    try {
      const response = await metricsAPI.export(format)
      if (format === 'csv') {
        const blob = new Blob([response.data], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'metrics.csv'
        a.click()
      } else {
        // JSON - show in new tab or download
        const blob = new Blob([JSON.stringify(response.data, null, 2)], {
          type: 'application/json',
        })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'metrics.json'
        a.click()
      }
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  const toggleTestRun = (id) => {
    setSelectedTestRuns((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Metrics & Analytics</h2>
        <div className="flex gap-2">
          <button
            onClick={() => handleExport('csv')}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            Export CSV
          </button>
          <button
            onClick={() => handleExport('json')}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            Export JSON
          </button>
        </div>
      </div>

      {/* Aggregate Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-500">Total Test Runs</p>
          <p className="text-3xl font-bold">
            {aggregateData?.data?.total_test_runs || 0}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-500">Documents Processed</p>
          <p className="text-3xl font-bold">
            {aggregateData?.data?.total_documents_processed || 0}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-500">Overall Accuracy</p>
          <p className="text-3xl font-bold text-blue-600">
            {((aggregateData?.data?.average_accuracy || 0) * 100).toFixed(1)}%
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-500">Fields Tracked</p>
          <p className="text-3xl font-bold">
            {fieldData?.data?.total_fields || 0}
          </p>
        </div>
      </div>

      {/* Performance by Library */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* By Layout Library */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">By Layout Library</h3>
          {aggregateLoading ? (
            <p>Loading...</p>
          ) : aggregateData?.data?.by_layout_library &&
            Object.keys(aggregateData.data.by_layout_library).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(aggregateData.data.by_layout_library).map(
                ([lib, accuracy]) => (
                  <div key={lib} className="flex items-center gap-3">
                    <span className="w-32 text-sm truncate">{lib}</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-4">
                      <div
                        className="bg-blue-500 h-4 rounded-full"
                        style={{ width: `${accuracy * 100}%` }}
                      />
                    </div>
                    <span className="w-16 text-sm text-right">
                      {(accuracy * 100).toFixed(1)}%
                    </span>
                  </div>
                )
              )}
            </div>
          ) : (
            <p className="text-gray-500">No data yet.</p>
          )}
        </div>

        {/* By OCR Library */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">By OCR Library</h3>
          {aggregateLoading ? (
            <p>Loading...</p>
          ) : aggregateData?.data?.by_ocr_library &&
            Object.keys(aggregateData.data.by_ocr_library).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(aggregateData.data.by_ocr_library).map(
                ([lib, accuracy]) => (
                  <div key={lib} className="flex items-center gap-3">
                    <span className="w-32 text-sm truncate">{lib}</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-4">
                      <div
                        className="bg-green-500 h-4 rounded-full"
                        style={{ width: `${accuracy * 100}%` }}
                      />
                    </div>
                    <span className="w-16 text-sm text-right">
                      {(accuracy * 100).toFixed(1)}%
                    </span>
                  </div>
                )
              )}
            </div>
          ) : (
            <p className="text-gray-500">No data yet.</p>
          )}
        </div>
      </div>

      {/* Per-Field Accuracy */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">Per-Field Accuracy</h3>
        {fieldLoading ? (
          <p>Loading...</p>
        ) : fieldData?.data?.fields &&
          Object.keys(fieldData.data.fields).length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="py-2">Field Name</th>
                  <th className="py-2">Accuracy</th>
                  <th className="py-2">Sample Count</th>
                  <th className="py-2">Visual</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(fieldData.data.fields).map(([field, data]) => (
                  <tr key={field} className="border-b">
                    <td className="py-2">{field}</td>
                    <td className="py-2">
                      <span
                        className={`font-medium ${
                          data.average_accuracy >= 0.8
                            ? 'text-green-600'
                            : data.average_accuracy >= 0.5
                            ? 'text-yellow-600'
                            : 'text-red-600'
                        }`}
                      >
                        {(data.average_accuracy * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-2">{data.sample_count}</td>
                    <td className="py-2 w-40">
                      <div className="bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            data.average_accuracy >= 0.8
                              ? 'bg-green-500'
                              : data.average_accuracy >= 0.5
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                          }`}
                          style={{ width: `${data.average_accuracy * 100}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500">No field data yet.</p>
        )}
      </div>

      {/* Compare Test Runs */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Compare Test Runs</h3>
        <p className="text-sm text-gray-600 mb-4">
          Select 2 or more test runs to compare:
        </p>

        {/* Test Run Selector */}
        <div className="flex flex-wrap gap-2 mb-4">
          {testsData?.data?.test_runs
            ?.filter((tr) => tr.status === 'completed')
            .map((run) => (
              <button
                key={run.id}
                onClick={() => toggleTestRun(run.id)}
                className={`px-3 py-1 rounded-full text-sm ${
                  selectedTestRuns.includes(run.id)
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                {run.layout_library} + {run.ocr_library}
              </button>
            ))}
        </div>

        {/* Comparison Results */}
        {comparisonData?.data?.comparisons?.length >= 2 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="py-2">Configuration</th>
                  <th className="py-2">Documents</th>
                  <th className="py-2">Accuracy</th>
                  <th className="py-2">Date</th>
                </tr>
              </thead>
              <tbody>
                {comparisonData.data.comparisons.map((comp) => (
                  <tr key={comp.test_run_id} className="border-b">
                    <td className="py-2 font-medium">
                      {comp.layout_library} + {comp.ocr_library}
                    </td>
                    <td className="py-2">{comp.document_count}</td>
                    <td className="py-2">
                      <span
                        className={`font-bold ${
                          comp.average_accuracy >= 0.8
                            ? 'text-green-600'
                            : comp.average_accuracy >= 0.5
                            ? 'text-yellow-600'
                            : 'text-red-600'
                        }`}
                      >
                        {(comp.average_accuracy * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-2">
                      {new Date(comp.started_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default MetricsPage
