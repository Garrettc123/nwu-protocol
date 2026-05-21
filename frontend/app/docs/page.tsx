import Link from 'next/link';

const sections = [
  {
    id: 'overview',
    title: 'Overview',
    content: `NWU Protocol is a decentralized intelligence marketplace. Developers and researchers
upload code, datasets, and documents; an AI verifier scores each contribution for
quality and originality; verified contributors earn NWU tokens as rewards. All
contribution metadata is pinned to IPFS for permanent, tamper-proof storage.`,
  },
  {
    id: 'getting-started',
    title: 'Getting Started',
    steps: [
      {
        label: 'Connect Wallet',
        body: `Click "Connect Wallet" in the nav bar. NWU Protocol uses EIP-4361 (Sign-In with
Ethereum) — you sign a message to prove wallet ownership. No gas is consumed.`,
      },
      {
        label: 'Upload a Contribution',
        body: `Go to Upload, choose a file (code, dataset, or document), add a title and
description, then submit. The file is hashed and stored on IPFS; the metadata is
submitted to the backend for AI verification.`,
      },
      {
        label: 'Earn NWU Rewards',
        body: `Verified contributions earn NWU token rewards proportional to the AI quality
score (0–100). Rewards accumulate in your wallet and can be viewed on the Wallet page.`,
      },
    ],
  },
  {
    id: 'contributions',
    title: 'Contributions',
    rows: [
      ['Status', 'Meaning'],
      ['pending', 'Queued for AI verification'],
      ['verifying', 'Currently being evaluated'],
      ['verified', 'Accepted — reward distributed'],
      ['rejected', 'Did not meet quality threshold'],
    ],
    footer: `The AI verifier checks for originality, relevance, and technical quality. Scores
above 60 are typically accepted. Rejected contributions may be resubmitted after
revision.`,
  },
  {
    id: 'api',
    title: 'API Access',
    content: `Each Pro or Enterprise subscription includes an API key for programmatic access.
The key is returned in the dashboard after a successful Stripe checkout.`,
    endpoints: [
      { method: 'GET', path: '/api/v1/contributions/', desc: 'List contributions (authenticated)' },
      { method: 'POST', path: '/api/v1/contributions/', desc: 'Upload a contribution' },
      { method: 'GET', path: '/api/v1/contributions/{id}', desc: 'Get contribution detail' },
      { method: 'GET', path: '/api/v1/users/{address}', desc: 'Get user profile' },
      { method: 'GET', path: '/api/v1/users/{address}/stats', desc: 'Contribution statistics' },
      { method: 'GET', path: '/api/v1/users/{address}/rewards', desc: 'Reward history' },
      { method: 'GET', path: '/api/v1/payments/pricing', desc: 'Available subscription tiers' },
      { method: 'POST', path: '/api/v1/payments/checkout-session', desc: 'Create Stripe checkout' },
      { method: 'GET', path: '/api/v1/referrals/stats', desc: 'Referral stats for authed user' },
      { method: 'POST', path: '/api/v1/referrals/generate', desc: 'Generate / fetch referral code' },
      { method: 'POST', path: '/api/v1/referrals/apply', desc: 'Apply a referral code on signup' },
      { method: 'POST', path: '/api/v1/referrals/claim', desc: 'Claim pending NWU referral rewards' },
    ],
  },
  {
    id: 'referrals',
    title: 'Referrals & Affiliates',
    content: `Share your referral link from the Referrals page. When someone signs up via
your link you earn 50 NWU. Reach 10 conversions to unlock Affiliate status,
which adds a 5–10% revenue share on every subscription your referrals purchase.
Pending NWU rewards can be claimed at any time from the Referrals page.`,
  },
  {
    id: 'pricing',
    title: 'Pricing',
    tiers: [
      {
        name: 'Free',
        price: '$0',
        limits: '100 API calls / day',
        note: 'Contributions + NWU rewards included.',
      },
      {
        name: 'Pro',
        price: '$99 / mo',
        limits: '10,000 API calls / day',
        note: 'Priority verification + dedicated API key.',
      },
      {
        name: 'Enterprise',
        price: '$999 / mo',
        limits: '100,000 API calls / day',
        note: 'SLA, custom integrations, revenue share.',
      },
    ],
  },
  {
    id: 'security',
    title: 'Security & Privacy',
    content: `Authentication uses JWT bearer tokens issued after wallet signature verification.
Contribution files are encrypted in transit (TLS) and stored on IPFS (content-
addressed, immutable). Stripe handles all payment data — NWU Protocol never stores
card numbers. API keys are bcrypt-hashed server-side; only the prefix is stored in
plaintext for lookup.`,
  },
];

export default function DocsPage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      <div className="max-w-5xl mx-auto px-4 py-16 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-5xl font-bold mb-3">Documentation</h1>
          <p className="text-gray-400 text-lg">
            Everything you need to build with NWU Protocol.
          </p>
        </div>

        {/* TOC */}
        <nav className="bg-gray-800 rounded-xl border border-gray-700 p-6 mb-12">
          <p className="text-xs uppercase tracking-wider text-gray-500 mb-3">On this page</p>
          <ul className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
            {sections.map(s => (
              <li key={s.id}>
                <a href={`#${s.id}`} className="text-blue-400 hover:text-blue-300 transition">
                  {s.title}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        {/* Sections */}
        <div className="space-y-16">
          {/* Overview */}
          <section id="overview">
            <h2 className="text-3xl font-bold mb-4">{sections[0].title}</h2>
            <p className="text-gray-300 leading-relaxed">{sections[0].content}</p>
          </section>

          {/* Getting Started */}
          <section id="getting-started">
            <h2 className="text-3xl font-bold mb-6">{sections[1].title}</h2>
            <div className="space-y-4">
              {sections[1].steps!.map((step, i) => (
                <div key={i} className="flex gap-5 bg-gray-800 rounded-xl border border-gray-700 p-6">
                  <div className="shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center font-bold text-sm">
                    {i + 1}
                  </div>
                  <div>
                    <p className="font-semibold mb-1">{step.label}</p>
                    <p className="text-gray-400 text-sm leading-relaxed">{step.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Contributions */}
          <section id="contributions">
            <h2 className="text-3xl font-bold mb-4">{sections[2].title}</h2>
            <div className="overflow-x-auto mb-4">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 text-xs uppercase tracking-wider border-b border-gray-700">
                    {sections[2].rows![0].map(h => (
                      <th key={h} className="pb-3 text-left pr-8">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {sections[2].rows!.slice(1).map(row => (
                    <tr key={row[0]}>
                      <td className="py-2 pr-8 font-mono text-blue-400">{row[0]}</td>
                      <td className="py-2 text-gray-300">{row[1]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-gray-400 text-sm leading-relaxed">{sections[2].footer}</p>
          </section>

          {/* API Access */}
          <section id="api">
            <h2 className="text-3xl font-bold mb-2">{sections[3].title}</h2>
            <p className="text-gray-400 text-sm mb-6">{sections[3].content}</p>
            <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 text-xs uppercase tracking-wider border-b border-gray-700 bg-gray-900/50">
                    <th className="px-4 py-3 text-left">Method</th>
                    <th className="px-4 py-3 text-left">Endpoint</th>
                    <th className="px-4 py-3 text-left hidden sm:table-cell">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {sections[3].endpoints!.map(ep => (
                    <tr key={ep.path} className="hover:bg-gray-700/30 transition">
                      <td className="px-4 py-2.5">
                        <span className={`font-mono text-xs font-bold px-2 py-0.5 rounded ${
                          ep.method === 'GET'
                            ? 'bg-green-900/60 text-green-300'
                            : 'bg-blue-900/60 text-blue-300'
                        }`}>
                          {ep.method}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 font-mono text-xs text-gray-300">{ep.path}</td>
                      <td className="px-4 py-2.5 text-gray-400 text-xs hidden sm:table-cell">{ep.desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-gray-500 text-xs mt-3">
              Base URL: <span className="font-mono text-gray-300">{process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</span>.
              All authenticated endpoints require <span className="font-mono text-gray-300">Authorization: Bearer &lt;token&gt;</span>.
            </p>
          </section>

          {/* Referrals */}
          <section id="referrals">
            <h2 className="text-3xl font-bold mb-4">{sections[4].title}</h2>
            <p className="text-gray-300 leading-relaxed">{sections[4].content}</p>
            <div className="mt-4">
              <Link
                href="/referrals"
                className="inline-block px-5 py-2.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-semibold transition"
              >
                Go to Referrals →
              </Link>
            </div>
          </section>

          {/* Pricing */}
          <section id="pricing">
            <h2 className="text-3xl font-bold mb-6">{sections[5].title}</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {sections[5].tiers!.map(tier => (
                <div
                  key={tier.name}
                  className="bg-gray-800 rounded-xl border border-gray-700 p-6"
                >
                  <p className="font-bold text-xl mb-1">{tier.name}</p>
                  <p className="text-2xl font-extrabold text-blue-400 mb-2">{tier.price}</p>
                  <p className="text-sm text-gray-300 mb-1">{tier.limits}</p>
                  <p className="text-xs text-gray-500">{tier.note}</p>
                </div>
              ))}
            </div>
            <div className="mt-4">
              <Link
                href="/pricing"
                className="inline-block px-5 py-2.5 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-semibold transition"
              >
                Compare Plans →
              </Link>
            </div>
          </section>

          {/* Security */}
          <section id="security">
            <h2 className="text-3xl font-bold mb-4">{sections[6].title}</h2>
            <p className="text-gray-300 leading-relaxed whitespace-pre-line">{sections[6].content}</p>
          </section>
        </div>

        {/* Footer CTA */}
        <div className="mt-20 bg-gray-800 rounded-2xl border border-gray-700 p-8 text-center">
          <h3 className="text-2xl font-bold mb-2">Still have questions?</h3>
          <p className="text-gray-400 mb-6">We're happy to help you get started.</p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link
              href="/upload"
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition text-sm"
            >
              Upload a Contribution
            </Link>
            <a
              href="mailto:support@nwuprotocol.com"
              className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-semibold transition text-sm"
            >
              Email Support
            </a>
          </div>
        </div>
      </div>
    </main>
  );
}
