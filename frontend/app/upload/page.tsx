'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import Link from 'next/link'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [fileType, setFileType] = useState<'code' | 'dataset' | 'document'>('code')
  const [userAddress, setUserAddress] = useState('')
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!file || !title || !userAddress) {
      setError('Please fill in all required fields')
      return
    }

    setUploading(true)
    setError(null)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('title', title)
      formData.append('description', description)
      formData.append('file_type', fileType)
      formData.append('user_address', userAddress)

      const response = await axios.post(
        `${API_URL}/api/v1/contributions/`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )

      setResult(response.data)
      // Reset form
      setFile(null)
      setTitle('')
      setDescription('')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload contribution')
    } finally {
      setUploading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      {/* Header */}
      <header className="border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <Link href="/" className="text-3xl font-bold bg-gradient-to-r from-primary-400 to-green-600 text-transparent bg-clip-text">
              NWU Protocol
            </Link>
            <nav className="flex gap-6">
              <Link href="/upload" className="text-primary-400 font-semibold">
                Upload
              </Link>
              <Link href="/contributions" className="hover:text-primary-400 transition">
                Contributions
              </Link>
              <Link href="/dashboard" className="hover:text-primary-400 transition">
                Dashboard
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-16 sm:px-6 lg:px-8">
        <h1 className="text-4xl font-bold mb-8">Upload Contribution</h1>

        {result && (
          <div className="mb-8 bg-green-900 border border-green-700 rounded-lg p-6">
            <h3 className="text-xl font-bold mb-2 text-green-300">✓ Upload Successful!</h3>
            <p className="mb-4">Your contribution has been submitted for verification.</p>
            <div className="space-y-2 text-sm">
              <div><strong>ID:</strong> {result.id}</div>
              <div><strong>IPFS Hash:</strong> {result.ipfs_hash}</div>
              <div><strong>Status:</strong> {result.status}</div>
            </div>
            <Link
              href={`/contributions/${result.id}`}
              className="mt-4 inline-block px-4 py-2 bg-green-700 hover:bg-green-600 rounded transition"
            >
              View Contribution
            </Link>
          </div>
        )}

        {error && (
          <div className="mb-8 bg-red-900 border border-red-700 rounded-lg p-4">
            <p className="text-red-300">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium mb-2">File *</label>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition ${
                isDragActive
                  ? 'border-primary-500 bg-primary-900/20'
                  : 'border-gray-600 hover:border-gray-500'
              }`}
            >
              <input {...getInputProps()} />
              {file ? (
                <div>
                  <p className="text-lg font-semibold">{file.name}</p>
                  <p className="text-sm text-gray-400 mt-1">
                    {(file.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-lg mb-2">📁 Drop file here or click to browse</p>
                  <p className="text-sm text-gray-400">
                    Upload code, datasets, or documents
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium mb-2">Title *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-primary-500"
              placeholder="e.g., Advanced ML Algorithm for Image Classification"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium mb-2">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-primary-500 h-32"
              placeholder="Describe your contribution..."
            />
          </div>

          {/* File Type */}
          <div>
            <label className="block text-sm font-medium mb-2">File Type *</label>
            <select
              value={fileType}
              onChange={(e) => setFileType(e.target.value as 'code' | 'dataset' | 'document')}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-primary-500"
              required
            >
              <option value="code">Code</option>
              <option value="dataset">Dataset</option>
              <option value="document">Document</option>
            </select>
          </div>

          {/* User Address */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Ethereum Address * (0x...)
            </label>
            <input
              type="text"
              value={userAddress}
              onChange={(e) => setUserAddress(e.target.value)}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-primary-500"
              placeholder="0x..."
              pattern="^0x[a-fA-F0-9]{40}$"
              required
            />
            <p className="text-xs text-gray-400 mt-1">
              Your Ethereum address for reward distribution
            </p>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={uploading}
            className="w-full px-6 py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg font-semibold transition"
          >
            {uploading ? 'Uploading...' : 'Submit Contribution'}
          </button>
        </form>
      </div>
    </main>
  )
}
