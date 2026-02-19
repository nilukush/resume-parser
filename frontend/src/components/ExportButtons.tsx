import { FileText, MessageCircle, Send, Mail } from 'lucide-react';

interface ExportButtonsProps {
  loading?: boolean;
  onExportPdf: () => Promise<void>;
  onExportWhatsapp: () => Promise<void>;
  onExportTelegram: () => Promise<void>;
  onExportEmail: () => Promise<void>;
}

export default function ExportButtons({
  loading = false,
  onExportPdf,
  onExportWhatsapp,
  onExportTelegram,
  onExportEmail,
}: ExportButtonsProps) {
  return (
    <div className="bg-white rounded-2xl shadow-2xl p-8">
      <h2 className="text-2xl font-bold text-navy-900 mb-6">Export As</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* PDF Export */}
        <button
          onClick={onExportPdf}
          disabled={loading}
          className="flex flex-col items-center gap-3 p-6 bg-navy-50 hover:bg-navy-100 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed group"
          aria-label="Export as PDF"
        >
          <div className="bg-navy-600 p-4 rounded-lg group-hover:bg-navy-700 transition-colors">
            <FileText className="h-6 w-6 text-white" />
          </div>
          <span className="font-medium text-navy-900">PDF</span>
        </button>

        {/* WhatsApp Export */}
        <button
          onClick={onExportWhatsapp}
          disabled={loading}
          className="flex flex-col items-center gap-3 p-6 bg-green-50 hover:bg-green-100 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed group"
          aria-label="Share on WhatsApp"
        >
          <div className="bg-green-600 p-4 rounded-lg group-hover:bg-green-700 transition-colors">
            <MessageCircle className="h-6 w-6 text-white" />
          </div>
          <span className="font-medium text-green-900">WhatsApp</span>
        </button>

        {/* Telegram Export */}
        <button
          onClick={onExportTelegram}
          disabled={loading}
          className="flex flex-col items-center gap-3 p-6 bg-blue-50 hover:bg-blue-100 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed group"
          aria-label="Share on Telegram"
        >
          <div className="bg-blue-500 p-4 rounded-lg group-hover:bg-blue-600 transition-colors">
            <Send className="h-6 w-6 text-white" />
          </div>
          <span className="font-medium text-blue-900">Telegram</span>
        </button>

        {/* Email Export */}
        <button
          onClick={onExportEmail}
          disabled={loading}
          className="flex flex-col items-center gap-3 p-6 bg-gold-50 hover:bg-gold-100 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed group"
          aria-label="Share via Email"
        >
          <div className="bg-gold-500 p-4 rounded-lg group-hover:bg-gold-600 transition-colors">
            <Mail className="h-6 w-6 text-white" />
          </div>
          <span className="font-medium text-gold-900">Email</span>
        </button>
      </div>
      <p className="text-sm text-gray-500 mt-4">
        Export your resume in various formats for easy sharing
      </p>
    </div>
  );
}
