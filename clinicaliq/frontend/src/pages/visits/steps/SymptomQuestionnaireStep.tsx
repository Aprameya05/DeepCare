import { ConditionalQuestionnaire } from '@/components/visit/ConditionalQuestionnaire';

export function SymptomQuestionnaireStep({ gender, initialSymptoms, onNext, onBack }: { 
  gender: string, 
  initialSymptoms?: string[], 
  onNext: (data: any) => void, 
  onBack: () => void 
}) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Symptom Assessment</h2>
      <p className="text-sm text-slate-500">Adaptive questionnaire based on patient demographics and reported symptoms.</p>
      
      <ConditionalQuestionnaire 
        gender={gender}
        initialSymptoms={initialSymptoms}
        onSubmit={onNext}
        onBack={onBack}
      />
    </div>
  );
}
