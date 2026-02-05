import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { syntheticAPI, testsAPI } from '../services/api'

function RunTestsPage() {
  const [selectedBatches, setSelectedBatches] = useState([])
  const [layoutLibrary, setLayoutLibrary] = useState('')
  const [ocrLibrary, setOcrLibrary] = useState('')
  const [runningTests, setRunningTests] = useState([]) // Track multiple running tests
  const [userFilter, setUserFilter] = useState('')

  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Fetch batches
  const { data: batchesData, isLoading: batchesLoading } = useQuery({
    queryKey: ['batches'],
    queryFn: () => syntheticAPI.listBatches(),
  })

  // Fetch test runs
  const { data: testsData, isLoading: testsLoading } = useQuery({
    queryKey: ['tests'],
    queryFn: () => testsAPI.list(),
  })

  // Fetch available libraries
  const { data: librariesData } = useQuery({
    queryKey: ['libraries'],
    queryFn: () => testsAPI.getLibraries(),
  })

  // Poll for all running test statuses
  const { data: runningStatusData } = useQuery({
    queryKey: ['running-test-statuses', runningTests],
    queryFn: async () => {
      const statuses = await Promise.all(
        runningTests.map(async (id) => {
          try {
            const res = await testsAPI.getStatus(id)
            return { id, ...res.data }
          } catch {
            return { id, status: 'failed', error_message: 'Failed to fetch status' }
          }
        })
      )
      return statuses
    },
    enabled: runningTests.length > 0,
    refetchInterval: (data) => {
      // Keep polling if any test is still running
      const anyRunning = data?.data?.some(
        (s) => s.status !== 'completed' && s.status !== 'failed'
      )
      return anyRunning ? 2000 : false
    },
  })

  // Handle status changes - remove completed/failed tests from running list
  useEffect(() => {
    if (runningStatusData?.data) {
      const finished = runningStatusData.data.filter(
        (s) => s.status === 'completed' || s.status === 'failed'
      )
      if (finished.length > 0) {
        setRunningTests((prev) =>
          prev.filter((id) => !finished.some((f) => f.id === id))
        )
        queryClient.invalidateQueries(['tests'])
      }
    }
  }, [runningStatusData, queryClient])

  // Auto-detect running tests on page load
  useEffect(() => {
    if (testsData?.data?.test_runs && runningTests.length === 0) {
      const running = testsData.data.test_runs
        .filter((r) => r.status === 'running')
        .map((r) => r.id)
      if (running.length > 0) {
        setRunningTests(running)
      }
    }
  }, [testsData]) // eslint-disable-line react-hooks/exhaustive-deps

  // Set default libraries when loaded
  useEffect(() => {
    if (librariesData?.data) {
      if (!layoutLibrary && librariesData.data.layout_libraries?.length > 0) {
        setLayoutLibrary(librariesData.data.layout_libraries[0])
      }
      if (!ocrLibrary && librariesData.data.ocr_libraries?.length > 0) {
        setOcrLibrary(librariesData.data.ocr_libraries[0])
      }
    }
  }, [librariesData, layoutLibrary, ocrLibrary])

  // Extract unique users from batches and test runs
  const allBatches = batchesData?.data?.batches || []
  const allTestRuns = testsData?.data?.test_runs || []
  const uniqueUsers = [...new Set([
    ...allBatches.map(b => b.created_by_name).filter(Boolean).map(n => n.split('@')[0]),
    ...allTestRuns.map(r => r.started_by_name).filter(Boolean).map(n => n.split('@')[0]),
  ])].sort()

  // Filter batches and test runs by user
  const filteredBatches = userFilter
    ? allBatches.filter(b => b.created_by_name && b.created_by_name.split('@')[0] === userFilter)
    : allBatches
  const filteredTestRuns = userFilter
    ? allTestRuns.filter(r => r.started_by_name && r.started_by_name.split('@')[0] === userFilter)
    : allTestRuns

  // Determine if selected batches are all handwritten
  const selectedBatchObjects = filteredBatches.filter(
    (b) => selectedBatches.includes(b.id)
  )
  const allHandwritten = selectedBatchObjects.length > 0 && selectedBatchObjects.every(
    (b) => b.batch_type === 'handwritten'
  )

  // Run tests mutation
  const runMutation = useMutation({
    mutationFn: () =>
      testsAPI.run(selectedBatches, allHandwritten ? '' : layoutLibrary, ocrLibrary),
    onSuccess: (response) => {
      setRunningTests((prev) => [...prev, response.data.id])
      queryClient.invalidateQueries(['tests'])
    },
  })

  const toggleBatch = (batchId) => {
    setSelectedBatches((prev) =>
      prev.includes(batchId)
        ? prev.filter((id) => id !== batchId)
        : [...prev, batchId]
    )
  }

  const handleRun = () => {
    if (selectedBatches.length > 0 && layoutLibrary && ocrLibrary) {
      runMutation.mutate()
    }
  }

  const handleCancel = async (testId) => {
    try {
      await testsAPI.cancel(testId)
      setRunningTests((prev) => prev.filter((id) => id !== testId))
      queryClient.invalidateQueries(['tests'])
    } catch (e) {
      console.error('Cancel failed', e)
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Run Tests</h2>

      {/* User Filter */}
      {uniqueUsers.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex items-end gap-4">
            <div className="min-w-[150px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">User</label>
              <select
                value={userFilter}
                onChange={(e) => {
                  setUserFilter(e.target.value)
                  setSelectedBatches([])
                }}
                className="w-full px-3 py-2 border rounded-md text-sm"
              >
                <option value="">All Users</option>
                {uniqueUsers.map((user) => (
                  <option key={user} value={user}>{user}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Running Tests Progress */}
      {runningStatusData?.data?.length > 0 && (
        <div className="space-y-3 mb-6">
          {runningStatusData.data.map((testStatus) => (
            <div
              key={testStatus.id}
              className="bg-blue-50 border border-blue-200 rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">
                  Test Running...{' '}
                  <span className="text-xs text-gray-500 font-normal">
                    {testStatus.id.slice(0, 8)}
                  </span>
                </span>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-blue-600">
                    {testStatus.processed_documents} /{' '}
                    {testStatus.total_documents} documents
                  </span>
                  <button
                    onClick={() => handleCancel(testStatus.id)}
                    className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
                  >
                    Cancel
                  </button>
                </div>
              </div>
              <div className="w-full bg-blue-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{
                    width: `${testStatus.progress_percent || 0}%`,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Test Configuration */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">Step 1: Select Batches</h3>

        {batchesLoading ? (
          <p>Loading batches...</p>
        ) : filteredBatches.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredBatches.map((batch) => (
              <div
                key={batch.id}
                onClick={() => toggleBatch(batch.id)}
                className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                  selectedBatches.includes(batch.id)
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-400'
                }`}
              >
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={selectedBatches.includes(batch.id)}
                    onChange={() => {}}
                    className="pointer-events-none"
                  />
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium">
                        {batch.batch_number} - {batch.form_name} - {new Date(batch.created_at).toLocaleDateString()}
                        {batch.created_by_name && ` - ${batch.created_by_name.split('@')[0]}`}
                      </h4>
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          batch.batch_type === 'handwritten'
                            ? 'bg-purple-100 text-purple-700'
                            : 'bg-blue-100 text-blue-700'
                        }`}
                      >
                        {batch.batch_type === 'handwritten' ? 'Handwritten' : 'Synthetic'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500">
                      {batch.count} docs
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600">
            No batches available. Generate synthetic data first.
          </p>
        )}
      </div>

      {/* Library Selection */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">Step 2: Select Libraries</h3>
        {allHandwritten && (
          <p className="text-sm text-purple-600 mb-4">
            Handwritten batches use full-text OCR only (no layout detection needed).
          </p>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {!allHandwritten && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Layout Detection Library
            </label>
            <select
              value={layoutLibrary}
              onChange={(e) => setLayoutLibrary(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
            >
              {librariesData?.data?.layout_libraries?.map((lib) => (
                <option key={lib} value={lib}>
                  {lib}
                </option>
              ))}
            </select>
          </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              OCR Library
            </label>
            <select
              value={ocrLibrary}
              onChange={(e) => setOcrLibrary(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
            >
              {librariesData?.data?.ocr_libraries?.map((lib) => (
                <option key={lib} value={lib}>
                  {lib}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Run Button */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Step 3: Run Tests</h3>
            <p className="text-sm text-gray-600">
              {selectedBatches.length} batch(es) selected
              {runningTests.length > 0 && (
                <span className="ml-2 text-blue-600">
                  • {runningTests.length} test(s) currently running
                </span>
              )}
            </p>
          </div>
          <button
            onClick={handleRun}
            disabled={
              selectedBatches.length === 0 ||
              !layoutLibrary ||
              !ocrLibrary ||
              runMutation.isPending
            }
            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {runMutation.isPending ? 'Starting...' : 'Run Tests'}
          </button>
        </div>

        {runMutation.isError && (
          <p className="text-red-600 text-sm mt-4">
            {runMutation.error?.response?.data?.detail || 'Failed to start tests'}
          </p>
        )}
      </div>

      {/* Previous Test Runs */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Previous Test Runs</h3>
        {testsLoading ? (
          <p>Loading...</p>
        ) : filteredTestRuns.length > 0 ? (
          <div className="space-y-3">
            {filteredTestRuns.map((run) => (
              <div
                key={run.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <div>
                  <p className="font-medium">
                    {run.layout_library || 'N/A'} + {run.ocr_library}
                    {run.started_by_name && ` - ${run.started_by_name.split('@')[0]}`}
                    {' - '}{new Date(run.started_at).toLocaleDateString()}
                  </p>
                  <p className="text-sm text-gray-600">
                    {run.total_documents} documents •{' '}
                    {new Date(run.started_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <span
                    className={`px-2 py-1 rounded text-sm ${
                      run.status === 'completed'
                        ? 'bg-green-100 text-green-700'
                        : run.status === 'running'
                        ? 'bg-blue-100 text-blue-700'
                        : run.status === 'failed'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {run.status}
                  </span>
                  {run.status === 'completed' && (
                    <button
                      onClick={() => navigate(`/results/${run.id}`)}
                      className="text-blue-600 hover:underline text-sm"
                    >
                      View Results
                    </button>
                  )}
                  {run.status === 'running' && (
                    <button
                      onClick={() => handleCancel(run.id)}
                      className="text-red-600 hover:underline text-sm"
                    >
                      Cancel
                    </button>
                  )}
                  {run.status === 'failed' && run.error_message && (
                    <span
                      className="text-red-500 text-xs max-w-xs truncate"
                      title={run.error_message}
                    >
                      {run.error_message}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600">No test runs yet.</p>
        )}
      </div>
    </div>
  )
}

export default RunTestsPage
