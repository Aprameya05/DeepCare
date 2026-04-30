import { VitalsForm } from '@/components/visit/VitalsForm';

export function VitalsStep({ initialData, onNext, onBack }: { initialData: any, onNext: (data: any) => void, onBack: () => void }) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Patient Vitals</h2>
      <p className="text-sm text-slate-500">Enter current vitals. Abnormal values will be flagged.</p>
      
      <VitalsForm 
        initialData={initialData}
        onSubmit={onNext}
        onBack={onBack}
      />
    </div>
  );
}
