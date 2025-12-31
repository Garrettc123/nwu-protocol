'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

export default function Home() {
  const [apiStatus, setApiStatus] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`)
      .then(res => res.json())
      .then(data => {
        setApiStatus(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to fetch API status:', err)
        setLoading(false)
      })
  }, [])

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      {/* Header */}
      <header className="border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-primary-400 to-green-600 text-transparent bg-clip-text">
              NWU Protocol
            </h1>
            <nav className="flex gap-6">
              <Link href="/upload" className="hover:text-primary-400 transition">
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

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 py-16 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-5xl font-bold mb-6">
            Decentralized Intelligence &<br />
            Verified Truth Protocol
          </h2>
          <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
            Safeguarding humanity through AI-powered verification and blockchain immutability.
            Contribute code, datasets, and documents to earn NWU tokens.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/upload"
              className="px-8 py-3 bg-primary-600 hover:bg-primary-700 rounded-lg font-semibold transition"
            >
              Start Contributing
            </Link>
            <Link
              href="/docs"
              className="px-8 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-semibold transition"
            >
              Learn More
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <div className="text-4xl mb-4">🔍</div>
            <h3 className="text-xl font-bold mb-2">AI Verification</h3>
            <p className="text-gray-400">
              Advanced AI agents verify quality, originality, and security of all contributions.
            </p>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <div className="text-4xl mb-4">🔗</div>
            <h3 className="text-xl font-bold mb-2">Blockchain Storage</h3>
            <p className="text-gray-400">
              Immutable verification results stored on-chain with IPFS file storage.
            </p>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <div className="text-4xl mb-4">💰</div>
            <h3 className="text-xl font-bold mb-2">Token Rewards</h3>
            <p className="text-gray-400">
              Earn NWU tokens based on contribution quality and community impact.
            </p>
          </div>
        </div>

        {/* API Status */}
        <div className="mt-16">
          <h3 className="text-2xl font-bold mb-4 text-center">System Status</h3>
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 max-w-2xl mx-auto">
            {loading ? (
              <div className="text-center text-gray-400">Loading...</div>
            ) : apiStatus ? (
              <div>
                <div className="flex justify-between items-center mb-4">
                  <span className="text-gray-300">Overall Status</span>
                  <span className={`px-3 py-1 rounded ${
                    apiStatus.status === 'healthy' 
                      ? 'bg-green-600' 
                      : 'bg-yellow-600'
                  }`}>
                    {apiStatus.status}
                  </span>
                </div>
                {apiStatus.checks && (
                  <div className="space-y-2">
                    {Object.entries(apiStatus.checks).map(([key, value]) => (
                      <div key={key} className="flex justify-between items-center">
                        <span className="text-gray-400 capitalize">{key}</span>
                        <span className={`w-3 h-3 rounded-full ${
                          value ? 'bg-green-500' : 'bg-red-500'
                        }`}></span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-red-400">
                Failed to connect to API
              </div>
            )}
          </div>
        </div>

        {/* How It Works */}
        <div className="mt-20">
          <h3 className="text-2xl font-bold mb-8 text-center">How It Works</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                1
              </div>
              <h4 className="font-semibold mb-2">Upload</h4>
              <p className="text-sm text-gray-400">Submit your code, dataset, or document</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                2
              </div>
              <h4 className="font-semibold mb-2">Verify</h4>
              <p className="text-sm text-gray-400">AI agents analyze and score your contribution</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                3
              </div>
              <h4 className="font-semibold mb-2">Store</h4>
              <p className="text-sm text-gray-400">Results recorded on blockchain via IPFS</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                4
              </div>
              <h4 className="font-semibold mb-2">Earn</h4>
              <p className="text-sm text-gray-400">Receive NWU tokens based on quality</p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-700 mt-20">
        <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
          <div className="text-center text-gray-400">
            <p>&copy; 2025 NWU Protocol. Safeguarding humanity through verified truth.</p>
            <div className="mt-4 flex justify-center gap-6">
              <a href="https://github.com/Garrettc123/nwu-protocol" target="_blank" className="hover:text-white transition">
                GitHub
              </a>
              <Link href="/docs" className="hover:text-white transition">
                Documentation
              </Link>
              <Link href="/api/docs" className="hover:text-white transition">
                API Docs
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </main>
  )
}
