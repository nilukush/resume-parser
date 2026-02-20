/**
 * PublicSharedResumePage.tsx
 *
 * PUBLIC VIEW: This page is for public viewers accessing a shared resume link.
 *
 * Route: /shared/{share_token}
 *
 * Features:
 * - Read-only resume data display
 * - Export buttons (PDF, WhatsApp, Telegram, Email)
 * - NO edit capabilities
 * - NO share settings
 * - NO "Back to Review" button
 */

import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Loader2,
  User,
  Briefcase,
  GraduationCap,
  Award,
  AlertCircle,
  Download,
  Share2,
  Mail,
} from 'lucide-react';
import { resumeAPI, PublicResumeData } from '../services/api';

export default function PublicSharedResumePage() {
  const { token } = useParams<{ token: string }>();

  const [resumeData, setResumeData] = useState<PublicResumeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportLoading, setExportLoading] = useState(false);

  useEffect(() => {
    if (token) {
      loadPublicResume(token);
    }
  }, [token]);

  const loadPublicResume = async (shareToken: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await resumeAPI.getPublicShare(shareToken);
      setResumeData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load shared resume');
    } finally {
      setLoading(false);
    }
  };

  const handleExportPdf = async () => {
    if (!resumeData?.resume_id) return;
    try {
      setExportLoading(true);
      const blob = await resumeAPI.exportPdf(resumeData.resume_id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${resumeData.personal_info.full_name?.replace(/\s+/g, '_') || 'resume'}_resume.pdf`;
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
    if (!resumeData?.resume_id) return;
    try {
      setExportLoading(true);
      const response = await resumeAPI.exportWhatsapp(resumeData.resume_id);
      window.open(response.whatsapp_url, '_blank');
    } catch (err) {
      console.error('Failed to export WhatsApp:', err);
    } finally {
      setExportLoading(false);
    }
  };

  const handleExportTelegram = async () => {
    if (!resumeData?.resume_id) return;
    try {
      setExportLoading(true);
      const response = await resumeAPI.exportTelegram(resumeData.resume_id);
      window.open(response.telegram_url, '_blank');
    } catch (err) {
      console.error('Failed to export Telegram:', err);
    } finally {
      setExportLoading(false);
    }
  };

  const handleExportEmail = async () => {
    if (!resumeData?.resume_id) return;
    try {
      setExportLoading(true);
      const response = await resumeAPI.exportEmail(resumeData.resume_id);
      window.open(response.mailto_url, '_blank');
    } catch (err) {
      console.error('Failed to export Email:', err);
    } finally {
      setExportLoading(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-navy-900 to-navy-700 flex items-center justify-center">
        <div className="text-center text-white">
          <Loader2 className="animate-spin h-16 w-16 mx-auto mb-4" />
          <p className="text-xl">Loading shared resume...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-navy-900 to-navy-700 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full mx-4">
          <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-800 text-center mb-2">
            Failed to Load Shared Resume
          </h2>
          <p className="text-gray-600 text-center">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-navy-900 to-navy-700 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-xl p-8 mb-6">
          <h1 className="text-3xl font-bold text-navy-900 mb-2">Shared Resume</h1>
          <p className="text-gray-600">Viewing a shared resume</p>
        </div>

        {/* Export Buttons */}
        <div className="bg-white rounded-lg shadow-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Export & Share</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <button
              onClick={handleExportPdf}
              disabled={exportLoading}
              className="flex items-center justify-center gap-2 bg-navy-900 text-white px-4 py-3 rounded-lg hover:bg-navy-800 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              <Download className="h-5 w-5" />
              Export as PDF
            </button>
            <button
              onClick={handleExportWhatsapp}
              disabled={exportLoading}
              className="flex items-center justify-center gap-2 bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              <Share2 className="h-5 w-5" />
              Share via WhatsApp
            </button>
            <button
              onClick={handleExportTelegram}
              disabled={exportLoading}
              className="flex items-center justify-center gap-2 bg-blue-500 text-white px-4 py-3 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              <Share2 className="h-5 w-5" />
              Share via Telegram
            </button>
            <button
              onClick={handleExportEmail}
              disabled={exportLoading}
              className="flex items-center justify-center gap-2 bg-gray-600 text-white px-4 py-3 rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              <Mail className="h-5 w-5" />
              Share via Email
            </button>
          </div>
        </div>

        {/* Personal Information */}
        <div className="bg-white rounded-lg shadow-xl p-8 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <User className="h-6 w-6 text-gold-500" />
            <h2 className="text-2xl font-bold text-gray-800">Personal Information</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {resumeData?.personal_info.full_name && (
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Full Name</label>
                <p className="text-lg font-semibold text-gray-900">
                  {resumeData.personal_info.full_name}
                </p>
              </div>
            )}
            {resumeData?.personal_info.email && (
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Email</label>
                <p className="text-lg text-gray-900">{resumeData.personal_info.email}</p>
              </div>
            )}
            {resumeData?.personal_info.phone && (
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Phone</label>
                <p className="text-lg text-gray-900">{resumeData.personal_info.phone}</p>
              </div>
            )}
            {resumeData?.personal_info.location && (
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Location</label>
                <p className="text-lg text-gray-900">{resumeData.personal_info.location}</p>
              </div>
            )}
            {resumeData?.personal_info.linkedin_url && (
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-600 mb-1">LinkedIn</label>
                <a
                  href={resumeData.personal_info.linkedin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-lg text-blue-600 hover:underline"
                >
                  {resumeData.personal_info.linkedin_url}
                </a>
              </div>
            )}
            {resumeData?.personal_info.portfolio_url && (
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-600 mb-1">Portfolio</label>
                <a
                  href={resumeData.personal_info.portfolio_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-lg text-blue-600 hover:underline"
                >
                  {resumeData.personal_info.portfolio_url}
                </a>
              </div>
            )}
          </div>
        </div>

        {/* Work Experience */}
        {resumeData?.work_experience && resumeData.work_experience.length > 0 && (
          <div className="bg-white rounded-lg shadow-xl p-8 mb-6">
            <div className="flex items-center gap-3 mb-6">
              <Briefcase className="h-6 w-6 text-gold-500" />
              <h2 className="text-2xl font-bold text-gray-800">Work Experience</h2>
            </div>
            <div className="space-y-6">
              {resumeData.work_experience.map((exp, index) => (
                <div key={index} className="border-l-4 border-navy-900 pl-4">
                  <h3 className="text-xl font-bold text-gray-900">{exp.title}</h3>
                  <p className="text-lg text-gray-700 font-semibold">{exp.company}</p>
                  <p className="text-sm text-gray-600">
                    {exp.location} • {exp.start_date} - {exp.end_date}
                  </p>
                  {exp.description && (
                    <p className="mt-2 text-gray-700">{exp.description}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Education */}
        {resumeData?.education && resumeData.education.length > 0 && (
          <div className="bg-white rounded-lg shadow-xl p-8 mb-6">
            <div className="flex items-center gap-3 mb-6">
              <GraduationCap className="h-6 w-6 text-gold-500" />
              <h2 className="text-2xl font-bold text-gray-800">Education</h2>
            </div>
            <div className="space-y-4">
              {resumeData.education.map((edu, index) => (
                <div key={index} className="border-l-4 border-gold-500 pl-4">
                  <h3 className="text-xl font-bold text-gray-900">{edu.degree}</h3>
                  <p className="text-lg text-gray-700 font-semibold">{edu.institution}</p>
                  <p className="text-sm text-gray-600">
                    {edu.location} • {edu.start_date} - {edu.end_date}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Skills */}
        {resumeData?.skills && (
          <div className="bg-white rounded-lg shadow-xl p-8 mb-6">
            <div className="flex items-center gap-3 mb-6">
              <Award className="h-6 w-6 text-gold-500" />
              <h2 className="text-2xl font-bold text-gray-800">Skills</h2>
            </div>

            {resumeData.skills.technical && resumeData.skills.technical.length > 0 && (
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Technical Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {resumeData.skills.technical.map((skill, index) => (
                    <span
                      key={index}
                      className="bg-navy-100 text-navy-900 px-3 py-1 rounded-full text-sm"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {resumeData.skills.soft && resumeData.skills.soft.length > 0 && (
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Soft Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {resumeData.skills.soft.map((skill, index) => (
                    <span
                      key={index}
                      className="bg-gray-100 text-gray-900 px-3 py-1 rounded-full text-sm"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {resumeData.skills.languages && resumeData.skills.languages.length > 0 && (
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Languages</h3>
                <div className="flex flex-wrap gap-2">
                  {resumeData.skills.languages.map((lang, index) => {
                    // Handle both string and object formats
                    const language = typeof lang === 'string' ? lang : lang.language;
                    const proficiency = typeof lang === 'object' && lang.proficiency;
                    return (
                      <span
                        key={index}
                        className="bg-blue-100 text-blue-900 px-3 py-1 rounded-full text-sm"
                      >
                        {language}{proficiency ? ` (${proficiency}/10)` : ''}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}

            {resumeData.skills.certifications && resumeData.skills.certifications.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Certifications</h3>
                <div className="flex flex-wrap gap-2">
                  {resumeData.skills.certifications.map((cert, index) => (
                    <span
                      key={index}
                      className="bg-gold-100 text-gold-900 px-3 py-1 rounded-full text-sm"
                    >
                      {cert}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
