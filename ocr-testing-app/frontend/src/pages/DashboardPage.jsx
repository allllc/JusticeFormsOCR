import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { formsAPI, syntheticAPI, testsAPI, metricsAPI } from '../services/api'

function StatCard({ title, value, icon, linkTo, linkText }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
        </div>
        <span className="text-3xl">{icon}</span>
      </div>
      {linkTo && (
        <Link
          to={linkTo}
          className="text-blue-600 text-sm hover:underline mt-4 inline-block"
        >
          {linkText} →
        </Link>
      )}
    </div>
  )
}

function DashboardPage() {
  // Fetch stats
  const { data: formsData } = useQuery({
    queryKey: ['forms'],
    queryFn: () => formsAPI.list(),
  })

  const { data: batchesData } = useQuery({
    queryKey: ['batches'],
    queryFn: () => syntheticAPI.listBatches(),
  })

  const { data: testsData } = useQuery({
    queryKey: ['tests'],
    queryFn: () => testsAPI.list(),
  })

  const { data: metricsData } = useQuery({
    queryKey: ['metrics-aggregate'],
    queryFn: () => metricsAPI.getAggregate(),
  })

  const formsCount = formsData?.data?.total || 0
  const batchesCount = batchesData?.data?.total || 0
  const testsCount = testsData?.data?.total || 0
  const avgAccuracy = metricsData?.data?.average_accuracy || 0

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Form Templates"
          value={formsCount}
          icon="📄"
          linkTo="/forms"
          linkText="Manage forms"
        />
        <StatCard
          title="Data Batches"
          value={batchesCount}
          icon="🔄"
          linkTo="/synthetic"
          linkText="Generate data"
        />
        <StatCard
          title="Test Runs"
          value={testsCount}
          icon="▶️"
          linkTo="/tests"
          linkText="Run tests"
        />
        <StatCard
          title="Avg. Accuracy"
          value={`${(avgAccuracy * 100).toFixed(1)}%`}
          icon="📈"
          linkTo="/metrics"
          linkText="View metrics"
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/forms"
            className="flex items-center gap-3 p-4 border rounded-lg hover:bg-gray-50 transition-colors"
          >
            <span className="text-2xl">📤</span>
            <div>
              <p className="font-medium">Upload Form</p>
              <p className="text-sm text-gray-600">Add a new form template</p>
            </div>
          </Link>

          <Link
            to="/synthetic"
            className="flex items-center gap-3 p-4 border rounded-lg hover:bg-gray-50 transition-colors"
          >
            <span className="text-2xl">🔄</span>
            <div>
              <p className="font-medium">Generate Data</p>
              <p className="text-sm text-gray-600">Create synthetic filled forms</p>
            </div>
          </Link>

          <Link
            to="/tests"
            className="flex items-center gap-3 p-4 border rounded-lg hover:bg-gray-50 transition-colors"
          >
            <span className="text-2xl">▶️</span>
            <div>
              <p className="font-medium">Run Tests</p>
              <p className="text-sm text-gray-600">Process batches with OCR</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow p-6 mt-6">
        <h3 className="text-lg font-semibold mb-4">Recent Test Runs</h3>
        {testsData?.data?.test_runs?.length > 0 ? (
          <div className="space-y-3">
            {testsData.data.test_runs.slice(0, 5).map((run) => (
              <div
                key={run.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <p className="font-medium">
                    {run.layout_library} + {run.ocr_library}
                  </p>
                  <p className="text-sm text-gray-600">
                    {new Date(run.started_at).toLocaleString()}
                  </p>
                </div>
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

export default DashboardPage
