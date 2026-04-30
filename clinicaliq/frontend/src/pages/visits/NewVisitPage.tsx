import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ChiefComplaintStep } from './steps/ChiefComplaintStep';
import { VitalsStep } from './steps/VitalsStep';
import { SymptomQuestionnaireStep } from './steps/SymptomQuestionnaireStep';
import { ReviewStep } from './steps/ReviewStep';
import { visitsApi } from '@/api/visits';
import { vitalsApi } from '@/api/vitals';
import { symptomsApi } from '@/api/symptoms';

export default function NewVisitPage() {
  const [step, setStep] = useState(1);
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  // Pass patientId via location state or query param
  const searchParams = new URLSearchParams(location.search);
  const patientId = searchParams.get('patientId');
  const gender = searchParams.get('gender') || 'male';

  const [visitId, setVisitId] = useState<string | null>(null);
  
  const [complaint, setComplaint] = useState('');
  const [vitals, setVitals] = useState<any>({});
  
  // Mutations
  const createVisit = useMutation({ mutationFn: visitsApi.create });
  const saveVitals = useMutation({ mutationFn: vitalsApi.create });
  const saveSymptoms = useMutation({ mutationFn: (data: any) => symptomsApi.submit(visitId!, data) });

  if (!patientId) {
    return <div className="p-8">No patient selected. Go back to patient list.</div>;
  }

  const handleComplaintNext = async (val: string) => {
    setComplaint(val);
    const visit = await createVisit.mutateAsync({ patient_id: patientId, chief_complaint: val });
    setVisitId(visit.id);
    setStep(2);
  };

  const handleVitalsNext = async (data: any) => {
    setVitals(data);
    await saveVitals.mutateAsync({ visit_id: visitId!, ...data });
    setStep(3);
  };

  const handleSymptomsNext = async (responses: any) => {
    await saveSymptoms.mutateAsync(responses);
    // Submit triggers the review
    setStep(4);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Progress Bar */}
      <div className="flex items-center gap-2 mb-8">
        {[1, 2, 3, 4].map((s) => (
          <div key={s} className="flex-1">
            <div className={`h-2 rounded-full ${step >= s ? 'bg-blue-600' : 'bg-slate-200'}`} />
            <p className={`text-xs mt-1 text-center ${step >= s ? 'text-blue-600 font-medium' : 'text-slate-400'}`}>
              {s === 1 ? 'Complaint' : s === 2 ? 'Vitals' : s === 3 ? 'Symptoms' : 'Review'}
            </p>
          </div>
        ))}
      </div>

      <div className="bg-white dark:bg-slate-950 p-6 rounded-xl border shadow-sm">
        {step === 1 && (
          <ChiefComplaintStep initialValue={complaint} onNext={handleComplaintNext} />
        )}
        {step === 2 && (
          <VitalsStep initialData={vitals} onNext={handleVitalsNext} onBack={() => setStep(1)} />
        )}
        {step === 3 && (
          <SymptomQuestionnaireStep 
            gender={gender} 
            initialSymptoms={[]} // could extract symptoms from complaint in a real app
            onNext={handleSymptomsNext} 
            onBack={() => setStep(2)} 
          />
        )}
        {step === 4 && visitId && (
          <ReviewStep visitId={visitId} />
        )}
      </div>
    </div>
  );
}
