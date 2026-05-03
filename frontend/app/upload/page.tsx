'use client';

import { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { useWallet } from '@/hooks/useWallet';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const getAuthHeaders = () => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export default function UploadPage() {
  const router = useRouter();
  const { address, connected } = useWallet();

  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [fileType, setFileType] = useState<'code' | 'dataset' | 'document'>('code');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!connected || !address) {
      router.push('/');
    }
  }, [connected, address, router]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) setFile(acceptedFiles[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, maxFiles: 1 });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !title || !address) {
      setError('Please fill in all required fields and connect your wallet');
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title);
      formData.append('description', description);
      formData.append('file_type', fileType);
      formData.append('user_address', address);

      const response = await axios.post(`${API_URL}/api/v1/contributions/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...getAuthHeaders(),
        },
      });

      setResult(response.data);
      setFile(null);
      setTitle('');
      setDescription('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload contribution');
    } finally {
      setUploading(false);
    }
  };

  if (!connected) return null;

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      <div className="max-w-4xl mx-auto px-4 py-16 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold">Upload Contribution</h1>
          <p className="text-gray-400 mt-2">
            Submitting as{' '}
            <span className="font-mono text-blue-400">
              {address?.substring(0, 6)}…{address?.substring(38)}
            </span>
          </p>
        </div>

        {result && (
          <div className="mb-8 bg-green-900/40 border border-green-700 rounded-lg p-6">
            <h3 className="text-xl font-bold mb-2 text-green-300">Upload Successful</h3>
            <p className="mb-4 text-gray-300">Your contribution is queued for AI verification.</p>
            <div className="space-y-1 text-sm text-gray-400 font-mono mb-4">
              <div>ID: {result.id}</div>
              {result.ipfs_hash && <div>IPFS: {result.ipfs_hash}</div>}
              <div>Status: {result.status}</div>
            </div>
            <Link
              href={`/contributions/${result.id}`}
              className="inline-block px-4 py-2 bg-green-700 hover:bg-green-600 rounded-lg transition text-sm font-semibold"
            >
              View Contribution
            </Link>
          </div>
        )}

        {error && (
          <div className="mb-8 bg-red-900/40 border border-red-700 rounded-lg p-4">
            <p className="text-red-300">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* File drop zone */}
          <div>
            <label className="block text-sm font-medium mb-2">File *</label>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition ${
                isDragActive
                  ? 'border-blue-500 bg-blue-900/20'
                  : 'border-gray-600 hover:border-gray-500'
              }`}
            >
              <input {...getInputProps()} />
              {file ? (
                <div>
                  <p className="text-lg font-semibold">{file.name}</p>
                  <p className="text-sm text-gray-400 mt-1">{(file.size / 1024).toFixed(2)} KB</p>
                </div>
              ) : (
                <div>
                  <p className="text-lg mb-2">Drop file here or click to browse</p>
                  <p className="text-sm text-gray-400">Code, datasets, or documents</p>
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Title *</label>
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-blue-500"
              placeholder="e.g., ML Algorithm for Image Classification"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Description</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-blue-500 h-28"
              placeholder="Describe your contribution…"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Type *</label>
            <select
              value={fileType}
              onChange={e => setFileType(e.target.value as 'code' | 'dataset' | 'document')}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-blue-500"
              required
            >
              <option value="code">Code</option>
              <option value="dataset">Dataset</option>
              <option value="document">Document</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={uploading}
            className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg font-semibold transition"
          >
            {uploading ? 'Uploading…' : 'Submit Contribution'}
          </button>
        </form>
      </div>
    </main>
  );
}
