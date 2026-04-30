import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { reportsApi } from '@/api/reports';
import { Button } from '@/components/ui/button';
import { FileDown, ArrowLeft } from 'lucide-react';

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: reportUrl, isLoading } = useQuery({
    queryKey: ['report', id],
    queryFn: async () => {
      await reportsApi.generate(id!);
      return `/api/reports/${id}/download`; // Mock URL for iframe preview
    },
    enabled: !!id,
  });

  const handleDownload = async () => {
    try {
      const blob = await reportsApi.download(id!);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `visit_report_${id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (err) {
      console.error('Download failed', err);
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div className="flex justify-between items-center shrink-0">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-4 h-4 mr-2" /> Back
          </Button>
          <h1 className="text-2xl font-bold">Clinical Report</h1>
        </div>
        <Button onClick={handleDownload} disabled={isLoading}>
          <FileDown className="w-4 h-4 mr-2" /> Download PDF
        </Button>
      </div>

      <div className="flex-1 border rounded-lg bg-slate-100 dark:bg-slate-900 overflow-hidden flex items-center justify-center min-h-[500px]">
        {isLoading ? (
          <p className="text-slate-500">Generating report...</p>
        ) : (
          <iframe 
            src={reportUrl} 
            className="w-full h-full bg-white" 
            title="PDF Preview"
            // Normally this would be a real PDF endpoint. For now we use a generic viewer if the endpoint isn't real.
          />
        )}
      </div>
    </div>
  );
}
