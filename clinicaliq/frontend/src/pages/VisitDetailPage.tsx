import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { visitsApi } from '@/api/visits';
import { ReviewStep } from './visits/steps/ReviewStep';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

export default function VisitDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: visit, isLoading } = useQuery({
    queryKey: ['visit', id],
    queryFn: () => visitsApi.get(id!),
    enabled: !!id,
  });

  if (isLoading) return <div className="p-8">Loading visit details...</div>;
  if (!visit) return <div className="p-8">Visit not found</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to={`/patients/${visit.patient_id}`}>
          <Button variant="outline">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Patient
          </Button>
        </Link>
        <h1 className="text-2xl font-bold tracking-tight">Visit Details</h1>
      </div>

      <div className="bg-white dark:bg-slate-950 p-6 rounded-xl border shadow-sm space-y-4 mb-6">
        <h2 className="text-lg font-semibold border-b pb-2">Chief Complaint</h2>
        <p>{visit.chief_complaint}</p>
      </div>

      <div className="bg-white dark:bg-slate-950 p-6 rounded-xl border shadow-sm">
        <ReviewStep visitId={id!} />
      </div>
    </div>
  );
}
