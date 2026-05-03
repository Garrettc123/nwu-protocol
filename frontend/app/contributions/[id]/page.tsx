'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const getAuthHeaders = () => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const STATUS_COLORS: Record<string, string> = {
  verified: 'bg-green-700 text-green-100',
  verifying: 'bg-yellow-700 text-yellow-100',
  rejected: 'bg-red-700 text-red-100',
  pending: 'bg-gray-700 text-gray-200',
};

export default function ContributionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [contribution, setContribution] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    axios
      .get(`${API_URL}/api/v1/contributions/${id}`, { headers: getAuthHeaders() })
      .then(res => {
        setContribution(res.data);
        setLoading(false);
      })
      .catch(() => {
        setError('Contribution not found or you do not have access.');
        setLoading(false);
      });
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto" />
          <p className="mt-4 text-gray-400">Loading contribution…</p>
        </div>
      </div>
    );
  }

  if (error || !contribution) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-lg mb-4">{error ?? 'Not found'}</p>
          <Link href="/contributions" className="text-blue-400 hover:underline">
            ← Back to Contributions
          </Link>
        </div>
      </div>
    );
  }

  const statusClass = STATUS_COLORS[contribution.status] ?? 'bg-gray-700 text-gray-200';

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      <div className="max-w-4xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
        {/* Breadcrumb */}
        <div className="mb-6">
          <Link href="/contributions" className="text-gray-400 hover:text-white text-sm transition">
            ← All Contributions
          </Link>
        </div>

        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold">{contribution.title}</h1>
            {contribution.description && (
              <p className="text-gray-400 mt-2">{contribution.description}</p>
            )}
          </div>
          <span className={`shrink-0 px-3 py-1 rounded-full text-sm font-semibold capitalize ${statusClass}`}>
            {contribution.status}
          </span>
        </div>

        {/* Metadata grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
            <p className="text-gray-400 text-xs uppercase tracking-wider">Type</p>
            <p className="text-lg font-semibold mt-1 capitalize">{contribution.file_type}</p>
          </div>
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
            <p className="text-gray-400 text-xs uppercase tracking-wider">Size</p>
            <p className="text-lg font-semibold mt-1">
              {contribution.file_size
                ? `${(contribution.file_size / 1024).toFixed(2)} KB`
                : '—'}
            </p>
          </div>
          {contribution.quality_score != null && (
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
              <p className="text-gray-400 text-xs uppercase tracking-wider">Quality Score</p>
              <p className="text-lg font-semibold mt-1 text-green-400">
                {contribution.quality_score}/100
              </p>
            </div>
          )}
          {contribution.reward_amount != null && (
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
              <p className="text-gray-400 text-xs uppercase tracking-wider">Reward</p>
              <p className="text-lg font-semibold mt-1 text-yellow-400">
                {Number(contribution.reward_amount).toFixed(2)} NWU
              </p>
            </div>
          )}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
            <p className="text-gray-400 text-xs uppercase tracking-wider">Submitted</p>
            <p className="text-lg font-semibold mt-1">
              {new Date(contribution.created_at).toLocaleDateString()}
            </p>
          </div>
          {contribution.user_address && (
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
              <p className="text-gray-400 text-xs uppercase tracking-wider">Contributor</p>
              <p className="text-sm font-mono mt-1 text-blue-400 truncate">
                {contribution.user_address.substring(0, 6)}…
                {contribution.user_address.substring(38)}
              </p>
            </div>
          )}
        </div>

        {/* IPFS hash */}
        {contribution.ipfs_hash && (
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-5 mb-6">
            <p className="text-gray-400 text-xs uppercase tracking-wider mb-1">IPFS Hash</p>
            <p className="font-mono text-sm text-gray-300 break-all">{contribution.ipfs_hash}</p>
          </div>
        )}

        {/* AI verification notes */}
        {contribution.verification_notes && (
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-5 mb-6">
            <h2 className="text-lg font-semibold mb-2">AI Verification Notes</h2>
            <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
              {contribution.verification_notes}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 flex-wrap">
          <a
            href={`${API_URL}/api/v1/contributions/${contribution.id}/file`}
            className="px-5 py-2.5 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-semibold transition"
            target="_blank"
            rel="noopener noreferrer"
          >
            Download File
          </a>
          {contribution.ipfs_hash && (
            <a
              href={`https://ipfs.io/ipfs/${contribution.ipfs_hash}`}
              className="px-5 py-2.5 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-semibold transition"
              target="_blank"
              rel="noopener noreferrer"
            >
              View on IPFS
            </a>
          )}
        </div>
      </div>
    </main>
  );
}
