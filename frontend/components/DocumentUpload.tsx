/**
 * Document Upload Component
 * 
 * Handles file upload with drag-and-drop support
 * Uploads files to backend for ingestion into vector database
 */

'use client'

import { useState, useRef } from 'react'
import axios from 'axios'
import { uploadDocument } from '@/lib/api'

interface DocumentUploadProps {
  onUploadSuccess?: () => void
}

export default function DocumentUpload({ onUploadSuccess }: DocumentUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFile = async (file: File) => {
    setUploading(true)
    setMessage(null)

    try {
      const response = await uploadDocument(file)
      setMessage({
        type: 'success',
        text: `${response.filename} uploaded! Created ${response.chunks_created} chunks.`,
      })
      
      if (onUploadSuccess) {
        onUploadSuccess()
      }

      setTimeout(() => setMessage(null), 5000)
    } catch (error: unknown) {
      let errorText = 'Failed to upload document'
      if (axios.isAxiosError(error)) {
        const apiDetail = error.response?.data?.detail
        if (typeof apiDetail === 'string' && apiDetail.trim().length > 0) {
          errorText = apiDetail
        } else if (error.message) {
          errorText = error.message
        }
      } else if (error instanceof Error && error.message) {
        errorText = error.message
      }
      setMessage({
        type: 'error',
        text: errorText,
      })
    } finally {
      setUploading(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
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

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const file = e.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  return (
    <div className="sketch-card p-6">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
          Upload Documents
        </h2>
        <span className="text-2xl">📄</span>
      </div>

      <div
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
          dragActive
            ? 'bg-green-50 scale-[1.02]'
            : 'hover:bg-gray-50'
        }`}
        style={{ 
          borderColor: dragActive ? 'var(--primary)' : 'var(--border-dark)',
          backgroundColor: dragActive ? 'var(--success-light)' : 'transparent'
        }}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.txt,.docx"
          onChange={handleFileChange}
          disabled={uploading}
        />

        {uploading ? (
          <div className="flex flex-col items-center">
            <div className="spinner w-12 h-12 mb-4"></div>
            <p style={{ color: 'var(--text-secondary)' }}>Processing document...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <div className="w-16 h-16 rounded-full bg-green-50 flex items-center justify-center mb-4" style={{ border: '2px solid var(--success-light)' }}>
              <span className="text-3xl">📄</span>
            </div>
            <p className="font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
              Drop files here or click to browse
            </p>
            <p className="text-sm mb-4" style={{ color: 'var(--text-tertiary)' }}>
              Supports PDF, TXT, and DOCX formats
            </p>
            <div className="flex gap-2 flex-wrap justify-center">
              <span className="badge">PDF</span>
              <span className="badge">TXT</span>
              <span className="badge">DOCX</span>
            </div>
          </div>
        )}
      </div>

      {message && (
        <div
          className={`mt-5 p-4 rounded-xl border ${
            message.type === 'success'
              ? 'bg-green-50 border-green-200'
              : 'bg-red-50 border-red-200'
          }`}
          style={{ 
            color: message.type === 'success' ? 'var(--primary-dark)' : 'var(--error)',
            boxShadow: 'var(--shadow-sm)'
          }}
        >
          <p className="text-sm font-medium">{message.text}</p>
        </div>
      )}
    </div>
  )
}
