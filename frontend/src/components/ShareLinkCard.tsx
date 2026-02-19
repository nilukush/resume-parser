import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

interface ShareLinkCardProps {
  shareUrl: string;
}

export default function ShareLinkCard({ shareUrl }: ShareLinkCardProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-2xl p-8">
      <h2 className="text-2xl font-bold text-navy-900 mb-6">Share Link</h2>
      <div className="flex items-center gap-3">
        <input
          type="text"
          value={shareUrl}
          readOnly
          className="flex-1 px-4 py-3 bg-navy-50 border border-navy-200 rounded-lg text-navy-900 font-mono text-sm"
        />
        <button
          onClick={handleCopy}
          className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors ${
            copied
              ? 'bg-green-600 text-white'
              : 'bg-navy-600 text-white hover:bg-navy-700'
          }`}
          aria-label={copied ? 'Copied!' : 'Copy link'}
        >
          {copied ? (
            <>
              <Check className="h-5 w-5" />
              <span>Copied!</span>
            </>
          ) : (
            <>
              <Copy className="h-5 w-5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <p className="text-sm text-gray-500 mt-3">
        Share this link to let others view your resume
      </p>
    </div>
  );
}
