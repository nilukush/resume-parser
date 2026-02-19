import { Clock, Eye, Trash2 } from 'lucide-react';

interface ShareSettingsProps {
  expiresAt: string;
  accessCount: number;
  isActive: boolean;
  onRevoke: () => void;
  loading?: boolean;
}

export default function ShareSettings({
  expiresAt,
  accessCount,
  isActive,
  onRevoke,
  loading = false,
}: ShareSettingsProps) {
  // Calculate days until expiration
  const calculateDaysUntilExpiry = (expiresAt: string): number => {
    const expiryDate = new Date(expiresAt);
    const now = new Date();
    const diffTime = expiryDate.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? diffDays : 0;
  };

  const daysUntilExpiry = calculateDaysUntilExpiry(expiresAt);

  return (
    <div className="bg-white rounded-2xl shadow-2xl p-8">
      <h2 className="text-2xl font-bold text-navy-900 mb-6">Share Settings</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Expiration */}
        <div className="flex items-center gap-4 bg-navy-50 p-4 rounded-lg">
          <div className="bg-navy-600 p-3 rounded-lg">
            <Clock className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm text-gray-600">Expires in</p>
            <p className="font-semibold text-navy-900">
              {daysUntilExpiry} {daysUntilExpiry === 1 ? 'day' : 'days'}
            </p>
          </div>
        </div>

        {/* Access Count */}
        <div className="flex items-center gap-4 bg-gold-50 p-4 rounded-lg">
          <div className="bg-gold-500 p-3 rounded-lg">
            <Eye className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm text-gray-600">Total views</p>
            <p className="font-semibold text-navy-900">{accessCount}</p>
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="mt-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className={`h-3 w-3 rounded-full ${
              isActive ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-sm text-gray-600">
            {isActive ? 'Active' : 'Revoked'}
          </span>
        </div>

        {/* Revoke Button */}
        {isActive && (
          <button
            onClick={onRevoke}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Revoke share link"
          >
            <Trash2 className="h-4 w-4" />
            <span>Revoke Link</span>
          </button>
        )}
      </div>

      {!isActive && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">
            This share link has been revoked and is no longer accessible.
          </p>
        </div>
      )}
    </div>
  );
}
