import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { syntheticAPI } from '../services/api'

function ViewDataPage() {
  const [selectedBatchId, setSelectedBatchId] = useState('')
  const [userFilter, setUserFilter] = useState('')
  const [currentDocIndex, setCurrentDocIndex] = useState(0)
  const [documentImageUrl, setDocumentImageUrl] = useState(null)
  const [imageLoading, setImageLoading] = useState(false)

  // Fetch all batches
  const { data: batchesData, isLoading: batchesLoading } = useQuery({
    queryKey: ['batches'],
    queryFn: () => syntheticAPI.listBatches(),
  })

  // Fetch selected batch details (includes documents)
  const { data: batchData, isLoading: batchLoading } = useQuery({
    queryKey: ['batch', selectedBatchId],
    queryFn: () => syntheticAPI.getBatch(selectedBatchId),
    enabled: !!selectedBatchId,
  })

  const batches = batchesData?.data?.batches || []
  const documents = batchData?.data?.documents || []

  // Extract unique users from batches
  const uniqueUsers = [...new Set(
    batches
      .map(b => b.created_by_name)
      .filter(Boolean)
      .map(name => name.split('@')[0])
  )].sort()

  // Filter batches by user
  const filteredBatches = userFilter
    ? batches.filter(b => b.created_by_name && b.created_by_name.split('@')[0] === userFilter)
    : batches

  // Reset doc index when batch changes
  useEffect(() => {
    setCurrentDocIndex(0)
    setDocumentImageUrl(null)
  }, [selectedBatchId])

  // Fetch document image when index changes
  useEffect(() => {
    if (selectedBatchId && documents.length > 0 && currentDocIndex < documents.length) {
      const doc = documents[currentDocIndex]
      setImageLoading(true)
      setDocumentImageUrl(null)
      syntheticAPI.getDocumentImage(selectedBatchId, doc.id)
        .then((url) => setDocumentImageUrl(url))
        .catch(() => setDocumentImageUrl(null))
        .finally(() => setImageLoading(false))
    } else {
      setDocumentImageUrl(null)
    }
    return () => {
      if (documentImageUrl) {
        URL.revokeObjectURL(documentImageUrl)
      }
    }
  }, [selectedBatchId, currentDocIndex, documents.length])

  const currentDoc = documents[currentDocIndex] || null

  const goToPrev = () => {
    if (currentDocIndex > 0) setCurrentDocIndex(currentDocIndex - 1)
  }
  const goToNext = () => {
    if (currentDocIndex < documents.length - 1) setCurrentDocIndex(currentDocIndex + 1)
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">View Data</h2>

      {/* Filter Bar */}
      <div className="bg-white rounded-lg shadow p-4 mb-4">
        <div className="flex flex-wrap items-end gap-4">
          {/* User Filter */}
          <div className="min-w-[180px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">User</label>
            <select
              value={userFilter}
              onChange={(e) => {
                setUserFilter(e.target.value)
                setSelectedBatchId('')
              }}
              className="w-full px-3 py-2 border rounded-md text-sm"
            >
              <option value="">All Users</option>
              {uniqueUsers.map((user) => (
                <option key={user} value={user}>{user}</option>
              ))}
            </select>
          </div>

          {/* Batch Dropdown */}
          <div className="flex-1 min-w-[300px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">Batch</label>
            <select
              value={selectedBatchId}
              onChange={(e) => setSelectedBatchId(e.target.value)}
              className="w-full px-3 py-2 border rounded-md text-sm"
            >
              <option value="">-- Select a batch --</option>
              {filteredBatches.map((batch) => (
                <option key={batch.id} value={batch.id}>
                  {batch.batch_number} - {batch.form_name}
                  {' - '}{new Date(batch.created_at).toLocaleDateString()}
                  {batch.created_by_name ? ` - ${batch.created_by_name.split('@')[0]}` : ''}
                  {` (${batch.count} docs)`}
                  {batch.batch_type === 'handwritten' ? ' [Handwritten]' : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Document count */}
          {selectedBatchId && documents.length > 0 && (
            <div className="text-sm text-gray-600 pb-2">
              Document {currentDocIndex + 1} of {documents.length}
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      {!selectedBatchId ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-600">Select a batch to view its documents.</p>
        </div>
      ) : batchLoading ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-500">Loading batch...</p>
        </div>
      ) : documents.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-600">No documents in this batch.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Left: Document Image with Carousel */}
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold">Document Image</h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={goToPrev}
                  disabled={currentDocIndex === 0}
                  className="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  Prev
                </button>
                <span className="text-sm text-gray-600 min-w-[60px] text-center">
                  {currentDocIndex + 1} / {documents.length}
                </span>
                <button
                  onClick={goToNext}
                  disabled={currentDocIndex === documents.length - 1}
                  className="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>

            {/* Thumbnail strip */}
            <div className="flex gap-1 mb-3 overflow-x-auto pb-2">
              {documents.map((doc, idx) => (
                <button
                  key={doc.id}
                  onClick={() => setCurrentDocIndex(idx)}
                  className={`flex-shrink-0 w-10 h-10 rounded border-2 text-xs font-medium flex items-center justify-center ${
                    idx === currentDocIndex
                      ? 'border-blue-600 bg-blue-50 text-blue-700'
                      : 'border-gray-200 bg-gray-50 text-gray-500 hover:border-gray-400'
                  }`}
                >
                  {idx + 1}
                </button>
              ))}
            </div>

            {/* Image display */}
            <div className="border rounded overflow-hidden">
              {imageLoading ? (
                <div className="p-8 text-center text-gray-500">Loading image...</div>
              ) : documentImageUrl ? (
                <img src={documentImageUrl} alt={`Document ${currentDocIndex + 1}`} className="w-full" />
              ) : (
                <div className="p-8 text-center text-gray-400">Image unavailable</div>
              )}
            </div>
          </div>

          {/* Right: Document Details */}
          <div className="space-y-4">
            {/* Document Info */}
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="font-semibold mb-3">Document Info</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Document ID:</span>
                  <span className="font-mono text-xs">{currentDoc?.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Batch:</span>
                  <span>{batchData?.data?.batch_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Form:</span>
                  <span>{batchData?.data?.form_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Type:</span>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    batchData?.data?.batch_type === 'handwritten'
                      ? 'bg-purple-100 text-purple-700'
                      : 'bg-blue-100 text-blue-700'
                  }`}>
                    {batchData?.data?.batch_type === 'handwritten' ? 'Handwritten' : 'Synthetic'}
                  </span>
                </div>
                {batchData?.data?.skew_preset && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Skew Preset:</span>
                    <span className="capitalize">{batchData.data.skew_preset}</span>
                  </div>
                )}
                {currentDoc?.is_skewed && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Skewed:</span>
                    <span className="text-green-600">Yes</span>
                  </div>
                )}
              </div>
            </div>

            {/* Field Values (for synthetic documents) */}
            {currentDoc?.field_values && Object.keys(currentDoc.field_values).length > 0 && (
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="font-semibold mb-3">Field Values (Ground Truth)</h3>
                <div className="space-y-2">
                  {Object.entries(currentDoc.field_values).map(([field, value]) => (
                    <div key={field} className="p-2 bg-gray-50 rounded text-sm">
                      <div className="flex justify-between">
                        <span className="font-medium text-gray-700">{field}</span>
                        <span className="font-mono">{value}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Empty state for handwritten (no field values) */}
            {currentDoc && (!currentDoc.field_values || Object.keys(currentDoc.field_values).length === 0) && (
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="font-semibold mb-3">Field Values</h3>
                <p className="text-sm text-gray-500 italic">
                  No ground truth fields. This is a {batchData?.data?.batch_type === 'handwritten' ? 'handwritten' : 'synthetic'} document.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default ViewDataPage
