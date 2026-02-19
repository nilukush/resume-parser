import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { resumeAPI, ParsedResumeData } from '../services/api';
import { Loader2, Edit2, Check, X, User, Briefcase, GraduationCap, Award, Share } from 'lucide-react';

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [resumeData, setResumeData] = useState<ParsedResumeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [sharing, setSharing] = useState(false);

  // Editable state for each section
  const [editingPersonal, setEditingPersonal] = useState(false);
  const [editedPersonal, setEditedPersonal] = useState<any>(null);

  useEffect(() => {
    if (id) {
      loadResumeData(id);
    }
  }, [id]);

  const loadResumeData = async (resumeId: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await resumeAPI.getResume(resumeId);

      if (response.data) {
        setResumeData(response.data);
        setEditedPersonal(response.data.personal_info);
      } else {
        setError('No resume data available');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load resume');
    } finally {
      setLoading(false);
    }
  };

  const handleSavePersonal = async () => {
    if (!id || !editedPersonal) return;

    try {
      setSaving(true);
      await resumeAPI.updateResume(id, { personal_info: editedPersonal });

      // Update local state
      setResumeData((prev) =>
        prev ? { ...prev, personal_info: { ...prev.personal_info, ...editedPersonal } } : null
      );

      setEditingPersonal(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save changes');
    } finally {
      setSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setEditedPersonal(resumeData?.personal_info || {});
    setEditingPersonal(false);
  };

  const handleShare = async () => {
    if (!id) return;

    try {
      setSharing(true);
      // Create share first, then navigate to share page
      await resumeAPI.createShare(id);
      navigate(`/share/${id}`);
    } catch (err) {
      console.error('Failed to create share:', err);
      setError(err instanceof Error ? err.message : 'Failed to create share link');
    } finally {
      setSharing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-navy-900 to-navy-700 flex items-center justify-center">
        <div className="text-center text-white">
          <Loader2 className="animate-spin h-16 w-16 mx-auto mb-4" />
          <p className="text-xl">Loading resume data...</p>
        </div>
      </div>
    );
  }

  if (error || !resumeData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-navy-900 to-navy-700 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Error</h1>
          <p className="text-gray-700 mb-6">{error || 'Failed to load resume'}</p>
          <button
            onClick={() => navigate('/')}
            className="w-full bg-navy-600 text-white py-3 rounded-lg hover:bg-navy-700 transition-colors"
          >
            Go Back to Upload
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
              <h1 className="text-4xl font-bold text-navy-900 mb-2">Review Your Resume</h1>
              <p className="text-gray-600">
                Review and edit the extracted information below
              </p>
            </div>
            {saveSuccess && (
              <div className="flex items-center text-green-600 bg-green-50 px-4 py-2 rounded-lg">
                <Check className="h-5 w-5 mr-2" />
                <span className="font-medium">Saved successfully!</span>
              </div>
            )}
          </div>
        </div>

        {/* Personal Information Section */}
        <SectionCard
          icon={<User className="h-6 w-6" />}
          title="Personal Information"
          isEditing={editingPersonal}
          onEdit={() => setEditingPersonal(true)}
          onSave={handleSavePersonal}
          onCancel={handleCancelEdit}
          saving={saving}
        >
          {editingPersonal ? (
            <PersonalInfoEdit
              data={editedPersonal}
              onChange={setEditedPersonal}
            />
          ) : (
            <PersonalInfoDisplay data={resumeData.personal_info} />
          )}
        </SectionCard>

        {/* Work Experience Section */}
        <SectionCard
          icon={<Briefcase className="h-6 w-6" />}
          title="Work Experience"
          showEditButton={false}
        >
          <WorkExperienceDisplay experiences={resumeData.work_experience} />
        </SectionCard>

        {/* Education Section */}
        <SectionCard
          icon={<GraduationCap className="h-6 w-6" />}
          title="Education"
          showEditButton={false}
        >
          <EducationDisplay education={resumeData.education} />
        </SectionCard>

        {/* Skills Section */}
        <SectionCard
          icon={<Award className="h-6 w-6" />}
          title="Skills"
          showEditButton={false}
        >
          <SkillsDisplay skills={resumeData.skills} />
        </SectionCard>

        {/* Confidence Scores */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 mt-6">
          <h2 className="text-2xl font-bold text-navy-900 mb-6">Parsing Confidence</h2>
          <ConfidenceScores scores={resumeData.confidence_scores} />
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between mt-8">
          <button
            onClick={() => navigate('/')}
            className="px-8 py-3 rounded-lg border-2 border-navy-600 text-navy-600 hover:bg-navy-50 transition-colors font-medium"
          >
            Upload Another Resume
          </button>
          <button
            onClick={handleShare}
            disabled={sharing}
            className="flex items-center gap-2 px-8 py-3 rounded-lg bg-gold-500 text-white hover:bg-gold-600 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {sharing ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Creating Share...
              </>
            ) : (
              <>
                <Share className="h-5 w-5" />
                Share Resume
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

// Section Card Component
interface SectionCardProps {
  icon: React.ReactNode;
  title: string;
  isEditing?: boolean;
  onEdit?: () => void;
  onSave?: () => void;
  onCancel?: () => void;
  saving?: boolean;
  showEditButton?: boolean;
  children: React.ReactNode;
}

function SectionCard({
  icon,
  title,
  isEditing = false,
  onEdit,
  onSave,
  onCancel,
  saving = false,
  showEditButton = true,
  children,
}: SectionCardProps) {
  return (
    <div className="bg-white rounded-2xl shadow-2xl p-8 mb-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <div className="bg-navy-100 p-3 rounded-lg mr-4 text-navy-600">
            {icon}
          </div>
          <h2 className="text-2xl font-bold text-navy-900">{title}</h2>
        </div>
        {showEditButton && !isEditing && onEdit && (
          <button
            onClick={onEdit}
            className="flex items-center px-4 py-2 text-navy-600 hover:bg-navy-50 rounded-lg transition-colors"
          >
            <Edit2 className="h-4 w-4 mr-2" />
            Edit
          </button>
        )}
        {isEditing && (
          <div className="flex gap-2">
            <button
              onClick={onCancel}
              disabled={saving}
              className="flex items-center px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
            >
              <X className="h-4 w-4 mr-2" />
              Cancel
            </button>
            <button
              onClick={onSave}
              disabled={saving}
              className="flex items-center px-4 py-2 bg-navy-600 text-white hover:bg-navy-700 rounded-lg transition-colors disabled:opacity-50"
            >
              {saving ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Check className="h-4 w-4 mr-2" />
              )}
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        )}
      </div>
      {children}
    </div>
  );
}

// Personal Info Display Component
function PersonalInfoDisplay({ data }: { data: any }) {
  const fields = [
    { label: 'Full Name', value: data.full_name },
    { label: 'Email', value: data.email },
    { label: 'Phone', value: data.phone },
    { label: 'Location', value: data.location },
    { label: 'LinkedIn', value: data.linkedin_url },
    { label: 'GitHub', value: data.github_url },
    { label: 'Portfolio', value: data.portfolio_url },
    { label: 'Summary', value: data.summary },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {fields.map((field) => (
        <div key={field.label} className="bg-navy-50 p-4 rounded-lg">
          <label className="text-sm font-medium text-gray-600">{field.label}</label>
          <p className="text-gray-900 mt-1 break-words">{field.value || '—'}</p>
        </div>
      ))}
    </div>
  );
}

// Personal Info Edit Component
function PersonalInfoEdit({ data, onChange }: { data: any; onChange: (data: any) => void }) {
  const handleChange = (field: string, value: string) => {
    onChange({ ...data, [field]: value });
  };

  const fields = [
    { label: 'Full Name', key: 'full_name', type: 'text' },
    { label: 'Email', key: 'email', type: 'email' },
    { label: 'Phone', key: 'phone', type: 'tel' },
    { label: 'Location', key: 'location', type: 'text' },
    { label: 'LinkedIn URL', key: 'linkedin_url', type: 'url' },
    { label: 'GitHub URL', key: 'github_url', type: 'url' },
    { label: 'Portfolio URL', key: 'portfolio_url', type: 'url' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {fields.map((field) => (
        <div key={field.key}>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {field.label}
          </label>
          <input
            type={field.type}
            value={data[field.key] || ''}
            onChange={(e) => handleChange(field.key, e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-navy-500 focus:border-transparent"
          />
        </div>
      ))}
      <div className="md:col-span-2">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Summary
        </label>
        <textarea
          value={data.summary || ''}
          onChange={(e) => handleChange('summary', e.target.value)}
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-navy-500 focus:border-transparent"
        />
      </div>
    </div>
  );
}

// Work Experience Display Component
function WorkExperienceDisplay({ experiences }: { experiences: any[] }) {
  if (experiences.length === 0) {
    return <p className="text-gray-500 italic">No work experience found</p>;
  }

  return (
    <div className="space-y-4">
      {experiences.map((exp, index) => (
        <div key={index} className="bg-navy-50 p-6 rounded-lg border-l-4 border-navy-600">
          <h3 className="text-xl font-bold text-navy-900">{exp.title}</h3>
          <p className="text-lg text-navy-700 font-medium">{exp.company}</p>
          <p className="text-sm text-gray-600 mt-1">
            {exp.location} • {exp.start_date} – {exp.end_date || 'Present'}
          </p>
          <p className="text-gray-700 mt-3">{exp.description}</p>
          {exp.confidence && (
            <div className="mt-3">
              <div className="flex items-center text-sm text-gray-500">
                <span className="mr-2">Confidence:</span>
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-navy-600 h-2 rounded-full"
                    style={{ width: `${exp.confidence}%` }}
                  />
                </div>
                <span className="ml-2">{exp.confidence}%</span>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// Education Display Component
function EducationDisplay({ education }: { education: any[] }) {
  if (education.length === 0) {
    return <p className="text-gray-500 italic">No education found</p>;
  }

  return (
    <div className="space-y-4">
      {education.map((edu, index) => (
        <div key={index} className="bg-navy-50 p-6 rounded-lg border-l-4 border-gold-500">
          <h3 className="text-xl font-bold text-navy-900">{edu.degree}</h3>
          <p className="text-lg text-navy-700 font-medium">{edu.institution}</p>
          <p className="text-sm text-gray-600 mt-1">
            {edu.field_of_study && `${edu.field_of_study} • `}
            {edu.location} • {edu.start_date} – {edu.end_date}
          </p>
          {edu.gpa && <p className="text-sm text-gray-600 mt-2">GPA: {edu.gpa}</p>}
          {edu.confidence && (
            <div className="mt-3">
              <div className="flex items-center text-sm text-gray-500">
                <span className="mr-2">Confidence:</span>
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-gold-500 h-2 rounded-full"
                    style={{ width: `${edu.confidence}%` }}
                  />
                </div>
                <span className="ml-2">{edu.confidence}%</span>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// Skills Display Component
function SkillsDisplay({ skills }: { skills: any }) {
  return (
    <div className="space-y-6">
      {skills.technical && skills.technical.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-navy-900 mb-3">Technical Skills</h3>
          <div className="flex flex-wrap gap-2">
            {skills.technical.map((skill: string, index: number) => (
              <span
                key={index}
                className="px-4 py-2 bg-navy-100 text-navy-700 rounded-full text-sm font-medium"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {skills.soft_skills && skills.soft_skills.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-navy-900 mb-3">Soft Skills</h3>
          <div className="flex flex-wrap gap-2">
            {skills.soft_skills.map((skill: string, index: number) => (
              <span
                key={index}
                className="px-4 py-2 bg-gold-100 text-gold-700 rounded-full text-sm font-medium"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {skills.certifications && skills.certifications.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-navy-900 mb-3">Certifications</h3>
          <div className="flex flex-wrap gap-2">
            {skills.certifications.map((cert: string, index: number) => (
              <span
                key={index}
                className="px-4 py-2 bg-green-100 text-green-700 rounded-full text-sm font-medium"
              >
                {cert}
              </span>
            ))}
          </div>
        </div>
      )}

      {skills.languages && skills.languages.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-navy-900 mb-3">Languages</h3>
          <div className="flex flex-wrap gap-2">
            {skills.languages.map((lang: string, index: number) => (
              <span
                key={index}
                className="px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-medium"
              >
                {lang}
              </span>
            ))}
          </div>
        </div>
      )}

      {skills.confidence && (
        <div className="mt-4">
          <div className="flex items-center text-sm text-gray-500">
            <span className="mr-2">Overall Confidence:</span>
            <div className="w-32 bg-gray-200 rounded-full h-2">
              <div
                className="bg-navy-600 h-2 rounded-full"
                style={{ width: `${skills.confidence}%` }}
              />
            </div>
            <span className="ml-2">{skills.confidence}%</span>
          </div>
        </div>
      )}
    </div>
  );
}

// Confidence Scores Component
function ConfidenceScores({ scores }: { scores: any }) {
  const scoreItems = [
    { label: 'Personal Information', key: 'personal_info', color: 'navy' },
    { label: 'Work Experience', key: 'work_experience', color: 'navy' },
    { label: 'Education', key: 'education', color: 'gold' },
    { label: 'Skills', key: 'skills', color: 'navy' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {scoreItems.map((item) => {
        const score = scores[item.key as keyof typeof scores];
        const colorClass = item.color === 'navy' ? 'bg-navy-600' : 'bg-gold-500';

        return (
          <div key={item.key}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">{item.label}</span>
              <span className="text-sm font-bold text-gray-900">{score}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`${colorClass} h-3 rounded-full transition-all duration-500`}
                style={{ width: `${score}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
