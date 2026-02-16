/**
 * Document List Component
 * 
 * Displays all uploaded documents
 * Allows deleting documents
 */

'use client'

import { useState, useEffect } from 'react'
import { getDocuments, deleteDocument } from '@/lib/api'

interface DocumentListProps {
  refreshTrigger?: number
}

export default function DocumentList({ refreshTrigger }: DocumentListProps) {
  const [documents, setDocuments] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState<string | null>(null)

  const fetchDocuments = async () => {
    try {
      setLoading(true)
      const response = await getDocuments()
      setDocuments(response.documents)
    } catch (error) {
      console.error('Failed to fetch documents:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [refreshTrigger])

  const handleDelete = async (filename: string) => {
    if (!confirm(`Delete ${filename}?`)) return

    try {
      setDeleting(filename)
      await deleteDocument(filename)
      await fetchDocuments()
    } catch (error) {
      console.error('Failed to delete:', error)
      alert('Failed to delete document')
    } finally {
      setDeleting(null)
    }
  }

  return (
    <div className="sketch-card sketch-card-alt p-6">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
            Your Documents
          </h2>
          <span className="px-3 py-1 rounded-full text-sm font-semibold" style={{ 
            backgroundColor: 'var(--success-light)', 
            color: 'var(--primary-dark)' 
          }}>
            {documents.length}
          </span>
        </div>
        <span className="text-xl">📚</span>
      </div>

      {loading ? (
        <div className="flex justify-center py-10">
          <div className="spinner w-10 h-10"></div>
        </div>
      ) : documents.length === 0 ? (
        <div className="text-center py-12 px-4 rounded-xl" style={{ backgroundColor: 'var(--bg-secondary)' }}>
          <div className="w-16 h-16 rounded-full bg-green-50 flex items-center justify-center mx-auto mb-4" style={{ border: '2px dashed var(--border-dark)' }}>
            <span className="text-3xl">📄</span>
          </div>
          <p className="font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>
            No documents yet
          </p>
          <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>
            Upload your first document to get started
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {documents.map((doc, index) => (
            <div
              key={index}
              className="group flex items-center justify-between p-4 rounded-xl border transition-all hover:shadow-md"
              style={{ 
                backgroundColor: 'var(--bg-card)',
                borderColor: 'var(--border)',
                transform: `rotate(${index % 2 === 0 ? '-0.5deg' : '0.5deg'})`,
              }}
              onMouseEnter={(e) => e.currentTarget.style.transform = 'rotate(0deg) translateY(-2px)'}
              onMouseLeave={(e) => e.currentTarget.style.transform = `rotate(${index % 2 === 0 ? '-0.5deg' : '0.5deg'})`}
            >
              <div className="flex items-center flex-1 min-w-0 gap-3">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'var(--success-light)' }}>
                  <span className="text-xl">📄</span>
                </div>
                <span className="text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }}>
                  {doc}
                </span>
              </div>
              
              <button
                onClick={() => handleDelete(doc)}
                disabled={deleting === doc}
                className="ml-3 p-2 rounded-lg transition-all opacity-0 group-hover:opacity-100 hover:bg-red-50 disabled:opacity-50"
                style={{ color: 'var(--error)' }}
                title="Delete document"
              >
                {deleting === doc ? (
                  <div className="spinner w-4 h-4"></div>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                )}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
