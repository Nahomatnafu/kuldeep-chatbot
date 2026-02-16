'use client'

import { useState } from 'react'
import DocumentUpload from '@/components/DocumentUpload'
import ChatInterface from '@/components/ChatInterface'
import DocumentList from '@/components/DocumentList'

export default function Home() {
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const handleUploadSuccess = () => {
    setRefreshTrigger(prev => prev + 1)
  }

  return (
    <main className="min-h-screen relative" style={{ zIndex: 2 }}>
      {/* Decorative leaf elements for aesthetic */}
      <div className="leaf float-animation" style={{ top: '8%', left: '5%', animationDelay: '0s' }}>🍃</div>
      <div className="leaf float-animation" style={{ top: '15%', right: '8%', animationDelay: '2s' }}>🌿</div>
      <div className="leaf float-animation" style={{ bottom: '20%', left: '10%', animationDelay: '4s' }}>🍃</div>
      <div className="leaf float-animation" style={{ top: '60%', right: '12%', animationDelay: '1s' }}>🌿</div>
      <div className="leaf float-animation" style={{ bottom: '15%', right: '5%', animationDelay: '3s' }}>🍂</div>
      
      <div className="container mx-auto px-4 py-8 relative fade-in">
        {/* Header with charming quote */}
        <header className="text-center mb-12 relative">
          <h1 className="text-5xl md:text-6xl handwritten mb-3 relative inline-block" style={{ color: 'var(--primary-dark)' }}>
            Knowledge Garden
            <svg className="absolute -bottom-2 left-0 w-full" height="8" viewBox="0 0 200 8">
              <path d="M 5 5 Q 100 2, 195 5" stroke="var(--primary)" strokeWidth="3" fill="none" strokeLinecap="round"/>
            </svg>
          </h1>
          <p className="text-xl mt-6" style={{ color: 'var(--text-secondary)' }}>
            Plant your documents, grow knowledge
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Panel - Document Management */}
          <div className="lg:col-span-1 space-y-6">
            <DocumentUpload onUploadSuccess={handleUploadSuccess} />
            <DocumentList refreshTrigger={refreshTrigger} />
          </div>

          {/* Right Panel - Chat Interface */}
          <div className="lg:col-span-2">
            <ChatInterface />
          </div>
        </div>
      </div>
    </main>
  )
}
