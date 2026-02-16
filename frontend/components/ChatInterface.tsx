/**
 * Chat Interface Component
 * 
 * Handles the conversation interface where users:
 * 1. Ask questions about their documents
 * 2. See AI-generated answers
 * 3. View source documents used for grounding
 */

'use client'

import { useEffect, useRef, useState } from 'react'
import { Message, SourceReference, queryDocuments } from '@/lib/api'

interface ChatMessage extends Message {
  sources?: SourceReference[]
}

export default function ChatInterface() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  } 

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: input,
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await queryDocuments(input, messages)
      
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error: any) {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `Error: ${error.response?.data?.detail || 'Failed to get response. Make sure documents are uploaded and API key is configured.'}`,
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="sketch-card flex flex-col h-[calc(100vh-12rem)]">
      {/* Chat Header */}
      <div className="px-6 py-5" style={{ borderBottom: `1px solid var(--border)` }}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
              Chat with Your Documents
            </h2>
            <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>
              Ask anything about your uploaded content
            </p>
          </div>
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center shadow-md">
            <span className="text-xl">💬</span>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-green-50 to-green-100 flex items-center justify-center mb-6 shadow-inner" style={{ border: '2px solid var(--success-light)' }}>
              <span className="text-4xl">💬</span>
            </div>
            <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
              Ready to help you
            </h3>
            <p className="text-sm max-w-md" style={{ color: 'var(--text-secondary)' }}>
              Upload some documents and start asking questions. I'll use RAG to find relevant information and provide accurate answers.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-8 max-w-xl">
              <div className="p-4 rounded-xl text-left" style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
                <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>Ask about content</p>
                <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>What are the key points in my document?</p>
              </div>
              <div className="p-4 rounded-xl text-left" style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
                <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>Get summaries</p>
                <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>Summarize the main findings</p>
              </div>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`flex items-start max-w-[80%] ${
                message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}
            >
              <div
                className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-sm ${
                  message.role === 'user' ? 'ml-3' : 'mr-3'
                }`}
                style={{ 
                  background: message.role === 'user' 
                    ? 'linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%)'
                    : 'linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%)',
                  border: '2px solid white'
                }}
              >
                <span className="text-lg">{message.role === 'user' ? '👤' : '🤖'}</span>
              </div>

              <div className="max-w-full">
                <div
                  className={`message-bubble px-5 py-3 ${
                    message.role === 'user' ? '' : ''
                  }`}
                  style={{ 
                    backgroundColor: message.role === 'user' ? 'var(--primary)' : 'var(--bg-card)',
                    color: message.role === 'user' ? 'white' : 'var(--text-primary)',
                    borderColor: message.role === 'user' ? 'transparent' : 'var(--border)',
                    fontSize: '15px',
                    lineHeight: '1.6'
                  }}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>

                {message.sources && message.sources.length > 0 && (
                  <div className="mt-3 p-3 rounded-lg" style={{ 
                    backgroundColor: 'var(--success-light)',
                    border: '1px solid var(--success)'
                  }}>
                    <p className="text-xs font-semibold mb-2" style={{ color: 'var(--primary-dark)' }}>
                      📚 Sources referenced:
                    </p>
                    <ul className="space-y-1">
                      {message.sources.map((source, idx) => (
                        <li key={idx} className="text-xs truncate flex items-center gap-2" style={{ color: 'var(--primary)' }}>
                          <span className="w-1 h-1 rounded-full" style={{ backgroundColor: 'var(--primary)' }}></span>
                          <a
                            href={`${API_URL}/documents/open/${encodeURIComponent(source.filename)}${source.page ? `#page=${source.page}` : ''}`}
                            target="_blank"
                            rel="noreferrer"
                            className="underline hover:no-underline"
                            title={source.page ? `Open ${source.filename} at page ${source.page}` : `Open ${source.filename}`}
                          >
                            {source.page ? `${source.filename} (page ${source.page})` : source.filename}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="flex items-start">
              <div className="flex-shrink-0 w-10 h-10 rounded-full mr-3 flex items-center justify-center shadow-sm" style={{ 
                background: 'linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%)',
                border: '2px solid white'
              }}>
                <span className="text-lg">🤖</span>
              </div>
              <div className="message-bubble px-5 py-3" style={{ 
                backgroundColor: 'var(--bg-card)',
                borderColor: 'var(--border)'
              }}>
                <div className="flex items-center gap-3">
                  <div className="spinner w-5 h-5"></div>
                  <span style={{ color: 'var(--text-secondary)' }}>Processing your question...</span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="px-6 py-5" style={{ borderTop: `1px solid var(--border)`, backgroundColor: 'var(--bg-secondary)' }}>
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your documents..."
            className="sketch-input flex-1"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="sketch-button flex items-center gap-2"
          >
            <span>Send</span>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  )
}
