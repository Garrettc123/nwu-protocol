'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ContributionsPage() {
  const [contributions, setContributions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get(`${API_URL}/api/v1/contributions/`)
      .then(res => {
        setContributions(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch contributions:', err);
        setLoading(false);
      });
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'verified':
        return 'bg-green-600';
      case 'verifying':
        return 'bg-yellow-600';
      case 'rejected':
        return 'bg-red-600';
      default:
        return 'bg-gray-600';
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      <header className="border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <Link
              href="/"
              className="text-3xl font-bold bg-gradient-to-r from-primary-400 to-green-600 text-transparent bg-clip-text"
            >
              NWU Protocol
            </Link>
            <nav className="flex gap-6">
              <Link href="/upload" className="hover:text-primary-400 transition">
                Upload
              </Link>
              <Link href="/contributions" className="text-primary-400 font-semibold">
                Contributions
              </Link>
              <Link href="/dashboard" className="hover:text-primary-400 transition">
                Dashboard
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-16 sm:px-6 lg:px-8">
        <h1 className="text-4xl font-bold mb-8">All Contributions</h1>

        {loading ? (
          <div className="text-center text-gray-400">Loading...</div>
        ) : contributions.length === 0 ? (
          <div className="text-center text-gray-400">
            <p className="mb-4">No contributions yet</p>
            <Link href="/upload" className="text-primary-400 hover:underline">
              Be the first to contribute!
            </Link>
          </div>
        ) : (
          <div className="grid gap-6">
            {contributions.map(contrib => (
              <div key={contrib.id} className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <h3 className="text-xl font-bold mb-2">{contrib.title}</h3>
                    <p className="text-gray-400 text-sm mb-3">{contrib.description}</p>
                    <div className="flex gap-4 text-sm text-gray-400">
                      <span className="capitalize">{contrib.file_type}</span>
                      <span>•</span>
                      <span>{(contrib.file_size / 1024).toFixed(2)} KB</span>
                      <span>•</span>
                      <span>ID: {contrib.id}</span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <span className={`px-3 py-1 rounded text-sm ${getStatusColor(contrib.status)}`}>
                      {contrib.status}
                    </span>
                    {contrib.quality_score && (
                      <span className="text-sm text-gray-400">
                        Score: {contrib.quality_score}/100
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex gap-3">
                  <a
                    href={`${API_URL}/api/v1/contributions/${contrib.id}/file`}
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded transition text-sm"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Download
                  </a>
                  <a
                    href={`https://ipfs.io/ipfs/${contrib.ipfs_hash}`}
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded transition text-sm"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    View on IPFS
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
