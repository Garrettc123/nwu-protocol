import type { Metadata } from 'next';
// import { Inter } from 'next/font/google';  // Disabled due to network restrictions
import { Analytics } from '@vercel/analytics/next';
import './globals.css';
import Link from 'next/link';
import WalletConnect from '@/components/WalletConnect';

export const metadata: Metadata = {
  title: 'NWU Protocol',
  description: 'Decentralized Intelligence & Verified Truth Protocol',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav className="bg-gray-900 border-b border-gray-800">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center gap-8">
                <Link href="/" className="text-xl font-bold text-white">
                  NWU Protocol
                </Link>
                <div className="flex gap-6">
                  <Link href="/upload" className="text-gray-300 hover:text-white transition">
                    Upload
                  </Link>
                  <Link href="/contributions" className="text-gray-300 hover:text-white transition">
                    Contributions
                  </Link>
                  <Link href="/pricing" className="text-gray-300 hover:text-white transition">
                    Pricing
                  </Link>
                  <Link href="/dashboard" className="text-gray-300 hover:text-white transition">
                    Dashboard
                  </Link>
                  <Link href="/wallet" className="text-gray-300 hover:text-white transition">
                    Wallet
                  </Link>
                  <Link href="/referrals" className="text-gray-300 hover:text-white transition">
                    Referrals
                  </Link>
                </div>
              </div>
              <WalletConnect />
            </div>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
