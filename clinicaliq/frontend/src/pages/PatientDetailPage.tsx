import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { patientsApi } from '@/api/patients';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Plus } from 'lucide-react';
import { format } from 'date-fns';

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: patient, isLoading: patientLoading } = useQuery({
    queryKey: ['patients', id],
    queryFn: () => patientsApi.get(id!),
    enabled: !!id,
  });

  const { data: visits, isLoading: visitsLoading } = useQuery({
    queryKey: ['patients', id, 'visits'],
    queryFn: () => patientsApi.getVisits(id!),
    enabled: !!id,
  });

  if (patientLoading) return <div className="p-8">Loading patient...</div>;
  if (!patient) return <div className="p-8">Patient not found</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{patient.name}</h1>
          <p className="text-slate-500">ID: {patient.id}</p>
        </div>
        <Button>Edit Patient</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Demographics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-slate-500">Age / Gender</p>
              <p className="font-medium">{patient.age} / {patient.gender}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Phone</p>
              <p className="font-medium">{patient.phone || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Medical History</p>
              <p className="font-medium">{patient.medical_history || 'None reported'}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-1 md:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Visit History</CardTitle>
            <Link to={`/visits/new?patientId=${patient.id}&gender=${patient.gender}`}>
              <Button variant="outline" size="sm">
                <Plus className="mr-2 h-4 w-4" /> New Visit
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {visitsLoading ? (
              <p className="text-slate-500">Loading visits...</p>
            ) : visits?.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <p>No previous visits</p>
                <Link to={`/visits/new?patientId=${patient.id}&gender=${patient.gender}`}>
                  <Button variant="link" className="mt-2">Create first visit</Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {visits?.map((visit) => (
                  <div key={visit.id} className="p-4 border rounded-lg flex justify-between items-center">
                    <div>
                      <p className="font-medium">{visit.chief_complaint}</p>
                      <p className="text-sm text-slate-500">
                        {format(new Date(visit.created_at), 'PPP')}
                      </p>
                    </div>
                    <div>
                      <Badge variant={visit.status === 'completed' ? 'secondary' : 'default'}>
                        {visit.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
