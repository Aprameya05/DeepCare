import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { overrideApi } from '@/api/override';
import { useMutation } from '@tanstack/react-query';

export function OverrideForm({ visitId, onOverrideSubmitted }: { visitId: string, onOverrideSubmitted: () => void }) {
  const [reason, setReason] = useState('');
  const [alternativeDiagnosis, setAlternativeDiagnosis] = useState('');

  const submitOverride = useMutation({
    mutationFn: (data: any) => overrideApi.submit(visitId, data),
    onSuccess: () => {
      onOverrideSubmitted();
    }
  });

  return (
    <Card className="border-amber-200 shadow-sm mt-6">
      <CardHeader className="bg-amber-50/50 pb-4">
        <CardTitle className="text-lg">Doctor Override (Optional)</CardTitle>
        <p className="text-sm text-slate-500">Use this to correct predictions and improve the system's accuracy.</p>
      </CardHeader>
      <CardContent className="space-y-4 pt-4">
        <div>
          <label htmlFor="alternative-diagnosis" className="text-sm font-medium mb-1 block">Alternative Diagnosis / Corrected Output</label>
          <Textarea 
            id="alternative-diagnosis"
            placeholder="Enter the correct diagnosis here..."
            value={alternativeDiagnosis}
            onChange={(e) => setAlternativeDiagnosis(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="override-reason" className="text-sm font-medium mb-1 block">Reason for Override</label>
          <Textarea 
            id="override-reason"
            placeholder="Briefly explain why the model was incorrect..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
        </div>
        <div className="flex justify-end">
          <Button 
            onClick={() => submitOverride.mutate({ reason, alternative_diagnosis: alternativeDiagnosis })}
            disabled={!alternativeDiagnosis || submitOverride.isPending}
            variant="default"
          >
            {submitOverride.isPending ? 'Submitting...' : 'Submit Override'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
