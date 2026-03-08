'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface PricingTier {
  name: string;
  display_name: string;
  price: number;
  currency: string;
  billing_period: string;
  features: string[];
  rate_limit: number;
}

export default function PricingPage() {
  const [tiers, setTiers] = useState<PricingTier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/payments/pricing`)
      .then((res) => res.json())
      .then((data) => {
        setTiers(data.tiers ?? []);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch pricing:', err);
        setError(true);
        setLoading(false);
      });
  }, []);

  const highlightedTier = 'pro';

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      <div className="max-w-7xl mx-auto px-4 py-20 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold mb-4">Simple, Transparent Pricing</h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Choose the plan that fits your needs. Upgrade or downgrade at any time.
          </p>
        </div>

        {/* Pricing Cards */}
        {loading ? (
          <div className="text-center text-gray-400 py-20">Loading pricing…</div>
        ) : error ? (
          <div className="text-center text-red-400 py-20">
            Failed to load pricing information. Please try again later.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {tiers.map((tier) => {
              const isHighlighted = tier.name === highlightedTier;
              return (
                <div
                  key={tier.name}
                  className={`relative rounded-2xl p-8 flex flex-col border ${
                    isHighlighted
                      ? 'border-primary-500 bg-primary-900/30 shadow-lg shadow-primary-500/20'
                      : 'border-gray-700 bg-gray-800'
                  }`}
                >
                  {isHighlighted && (
                    <span className="absolute -top-4 left-1/2 -translate-x-1/2 bg-primary-600 text-white text-xs font-semibold px-4 py-1 rounded-full">
                      Most Popular
                    </span>
                  )}

                  <h2 className="text-2xl font-bold mb-2">{tier.display_name}</h2>

                  <div className="flex items-end gap-1 mb-6">
                    {tier.price === 0 ? (
                      <span className="text-4xl font-extrabold">Free</span>
                    ) : (
                      <>
                        <span className="text-4xl font-extrabold">${tier.price}</span>
                        <span className="text-gray-400 mb-1">/ {tier.billing_period}</span>
                      </>
                    )}
                  </div>

                  <ul className="space-y-3 mb-8 flex-1">
                    {tier.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-2 text-gray-300">
                        <span className="text-green-400 mt-0.5">✓</span>
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <Link
                    href={tier.price === 0 ? '/upload' : `/dashboard?plan=${tier.name}`}
                    className={`block text-center py-3 rounded-lg font-semibold transition ${
                      isHighlighted
                        ? 'bg-primary-600 hover:bg-primary-700 text-white'
                        : 'bg-gray-700 hover:bg-gray-600 text-white'
                    }`}
                  >
                    {tier.price === 0 ? 'Get Started Free' : `Start ${tier.display_name}`}
                  </Link>
                </div>
              );
            })}
          </div>
        )}

        {/* FAQ / CTA */}
        <div className="mt-20 text-center">
          <h2 className="text-3xl font-bold mb-4">Have questions?</h2>
          <p className="text-gray-300 mb-6">
            Read the docs or reach out — we're happy to help you pick the right plan.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/docs"
              className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-semibold transition"
            >
              Read Docs
            </Link>
            <a
              href="mailto:support@nwuprotocol.com"
              className="px-6 py-3 bg-primary-600 hover:bg-primary-700 rounded-lg font-semibold transition"
            >
              Contact Us
            </a>
          </div>
        </div>
      </div>
    </main>
  );
}
