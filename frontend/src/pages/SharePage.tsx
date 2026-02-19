import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Loader2,
  User,
  Briefcase,
  GraduationCap,
  Award,
  AlertCircle,
  ArrowLeft,
} from 'lucide-react';
import { resumeAPI, ShareDetails, ParsedResumeData } from '../services/api';
import ShareLinkCard from '../components/ShareLinkCard';
import ExportButtons from '../components/ExportButtons';
import ShareSettings from '../components/ShareSettings';

export default function SharePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [shareData, setShareData] = useState<ShareDetails | null>(null);
  const [resumeData, setResumeData] = useState<ParsedResumeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportLoading, setExportLoading] = useState(false);
  const [revokeLoading, setRevokeLoading] = useState(false);

  useEffect(() => {
    if (id) {
      loadShareData(id);
    }
  }, [id]);

  const loadShareData = async (resumeId: string) => {
    try {
      setLoading(true);
      setError(null);

      // Load share details
      const shareResponse = await resumeAPI.getShare(resumeId);
      setShareData(shareResponse);

      // Load resume data
      const resumeResponse = await resumeAPI.getResume(resumeId);
      if (resumeResponse.data) {
        setResumeData(resumeResponse.data);
      } else {
        setError('No resume data available');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load share data');
    } finally {
      setLoading(false);
    }
  };

  const handleExportPdf = async () => {
    if (!id) return;
    try {
      setExportLoading(true);
      const blob = await resumeAPI.exportPdf(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${resumeData?.personal_info.full_name?.replace(/\s+/g, '_') || 'resume'}_resume.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export PDF:', err);
    } finally {
      setExportLoading(false);
    }
  };

  const handleExportWhatsapp = async () => {
    if (!id) return;
    try {
      setExportLoading(true);
      const response = await resumeAPI.exportWhatsapp(id);
      window.open(response.whatsapp_url, '_blank');
    } catch (err) {
      console.error('Failed to export WhatsApp:', err);
    } finally {
      setExportLoading(false);
    }
  };

  const handleExportTelegram = async () => {
    if (!id) return;
    try {
      setExportLoading(true);
      const response = await resumeAPI.exportTelegram(id);
      window.open(response.telegram_url, '_blank');
    } catch (err) {
      console.error('Failed to export Telegram:', err);
    } finally {
      setExportLoading(false);
    }
  };

  const handleExportEmail = async () => {
    if (!id) return;
    try {
      setExportLoading(true);
      const response = await resumeAPI.exportEmail(id);
      window.open(response.mailto_url, '_blank');
    } catch (err) {
      console.error('Failed to export Email:', err);
    } finally {
      setExportLoading(false);
    }
  };

  const handleRevoke = async () => {
    if (!id) return;
    try {
      setRevokeLoading(true);
      await resumeAPI.revokeShare(id);
      // Reload share data
      await loadShareData(id);
    } catch (err) {
      console.error('Failed to revoke share:', err);
    } finally {
      setRevokeLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-navy-900 to-navy-700 flex items-center justify-center">
        <div className="text-center text-white">
          <Loader2 className="animate-spin h-16 w-16 mx-auto mb-4" />
          <p className="text-xl">Loading share settings...</p>
        </div>
      </div>
    );
  }

  if (error || !shareData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-navy-900 to-navy-700 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
          <div className="flex items-center gap-3 text-red-600 mb-4">
            <AlertCircle className="h-8 w-8" />
            <h1 className="text-2xl font-bold">Error</h1>
          </div>
          <p className="text-gray-700 mb-6">{error || 'Failed to load share data'}</p>
          <button
            onClick={() => navigate(`/review/${id}`)}
            className="w-full bg-navy-600 text-white py-3 rounded-lg hover:bg-navy-700 transition-colors"
          >
            Go Back to Review
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-navy-900 to-navy-700 py-8 px-4">
      <div className="container mx-auto max-w-6xl">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <button
                onClick={() => navigate(`/review/${id}`)}
                className="flex items-center gap-2 text-navy-600 hover:text-navy-700 mb-4 transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                <span className="text-sm font-medium">Back to Review</span>
              </button>
              <h1 className="text-4xl font-bold text-navy-900 mb-2">Share Your Resume</h1>
              <p className="text-gray-600">
                Create a shareable link and export your resume in various formats
              </p>
            </div>
          </div>
        </div>

        {/* Share Link Card */}
        <ShareLinkCard shareUrl={shareData.share_url} />

        {/* Export Buttons */}
        <div className="mt-6">
          <ExportButtons
            loading={exportLoading}
            onExportPdf={handleExportPdf}
            onExportWhatsapp={handleExportWhatsapp}
            onExportTelegram={handleExportTelegram}
            onExportEmail={handleExportEmail}
          />
        </div>

        {/* Share Settings */}
        <div className="mt-6">
          <ShareSettings
            expiresAt={shareData.expires_at}
            accessCount={shareData.access_count}
            isActive={shareData.is_active}
            onRevoke={handleRevoke}
            loading={revokeLoading}
          />
        </div>

        {/* Resume Preview */}
        {resumeData && (
          <div className="bg-white rounded-2xl shadow-2xl p-8 mt-6">
            <h2 className="text-2xl font-bold text-navy-900 mb-6">Resume Preview</h2>

            {/* Personal Info */}
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-4">
                <User className="h-5 w-5 text-navy-600" />
                <h3 className="text-lg font-semibold text-navy-900">Personal Information</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {resumeData.personal_info.full_name && (
                  <div className="bg-navy-50 p-3 rounded-lg">
                    <span className="text-sm text-gray-600">Name</span>
                    <p className="font-medium text-navy-900">{resumeData.personal_info.full_name}</p>
                  </div>
                )}
                {resumeData.personal_info.email && (
                  <div className="bg-navy-50 p-3 rounded-lg">
                    <span className="text-sm text-gray-600">Email</span>
                    <p className="font-medium text-navy-900">{resumeData.personal_info.email}</p>
                  </div>
                )}
                {resumeData.personal_info.phone && (
                  <div className="bg-navy-50 p-3 rounded-lg">
                    <span className="text-sm text-gray-600">Phone</span>
                    <p className="font-medium text-navy-900">{resumeData.personal_info.phone}</p>
                  </div>
                )}
                {resumeData.personal_info.location && (
                  <div className="bg-navy-50 p-3 rounded-lg">
                    <span className="text-sm text-gray-600">Location</span>
                    <p className="font-medium text-navy-900">{resumeData.personal_info.location}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Work Experience */}
            {resumeData.work_experience.length > 0 && (
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-4">
                  <Briefcase className="h-5 w-5 text-navy-600" />
                  <h3 className="text-lg font-semibold text-navy-900">Work Experience</h3>
                </div>
                <div className="space-y-3">
                  {resumeData.work_experience.map((exp, index) => (
                    <div key={index} className="bg-navy-50 p-4 rounded-lg border-l-4 border-navy-600">
                      <h4 className="font-semibold text-navy-900">{exp.title}</h4>
                      <p className="text-sm text-navy-700">{exp.company}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Education */}
            {resumeData.education.length > 0 && (
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-4">
                  <GraduationCap className="h-5 w-5 text-gold-600" />
                  <h3 className="text-lg font-semibold text-navy-900">Education</h3>
                </div>
                <div className="space-y-3">
                  {resumeData.education.map((edu, index) => (
                    <div key={index} className="bg-gold-50 p-4 rounded-lg border-l-4 border-gold-500">
                      <h4 className="font-semibold text-navy-900">{edu.degree}</h4>
                      <p className="text-sm text-navy-700">{edu.institution}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Skills */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Award className="h-5 w-5 text-navy-600" />
                <h3 className="text-lg font-semibold text-navy-900">Skills</h3>
              </div>
              {resumeData.skills.technical && resumeData.skills.technical.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {resumeData.skills.technical.map((skill, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-navy-100 text-navy-700 rounded-full text-sm font-medium"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
