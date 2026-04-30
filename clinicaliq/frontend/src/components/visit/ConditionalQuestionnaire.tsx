import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { symptomsApi } from '@/api/symptoms';
import { SymptomQuestion } from './SymptomQuestion';
import { Button } from '@/components/ui/button';

interface ConditionalQuestionnaireProps {
  gender: string;
  initialSymptoms?: string[];
  onSubmit: (responses: Record<string, any>) => void;
  onBack: () => void;
}

export function ConditionalQuestionnaire({ gender, initialSymptoms = [], onSubmit, onBack }: ConditionalQuestionnaireProps) {
  const [responses, setResponses] = useState<Record<string, any>>({});
  
  const { data: questions, isLoading } = useQuery({
    queryKey: ['questions', gender, initialSymptoms],
    queryFn: () => symptomsApi.getQuestions(gender, initialSymptoms),
  });

  // Automatically fetch more questions if a boolean answer reveals new paths
  const activeSymptoms = [...initialSymptoms, ...Object.keys(responses).filter(k => responses[k] === true)];

  const { data: followUpQuestions } = useQuery({
    queryKey: ['questions', gender, activeSymptoms],
    queryFn: () => symptomsApi.getQuestions(gender, activeSymptoms),
    enabled: activeSymptoms.length > initialSymptoms.length,
  });

  const allQuestions = [...(questions || []), ...(followUpQuestions || [])].filter((q, idx, self) => 
    self.findIndex(t => t.id === q.id) === idx
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(responses);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {isLoading ? (
        <p className="text-slate-500">Loading questionnaire...</p>
      ) : (
        <div className="space-y-4">
          {allQuestions.map(q => (
            <SymptomQuestion
              key={q.id}
              question={q}
              value={responses[q.id]}
              onChange={(val) => setResponses(prev => ({ ...prev, [q.id]: val }))}
            />
          ))}
        </div>
      )}
      <div className="flex justify-between">
        <Button type="button" variant="outline" onClick={onBack}>Back</Button>
        <Button type="submit">Submit Intake</Button>
      </div>
    </form>
  );
}
