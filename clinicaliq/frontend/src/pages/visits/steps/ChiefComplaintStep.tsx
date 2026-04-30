import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';

export function ChiefComplaintStep({ initialValue, onNext }: { initialValue: string, onNext: (val: string) => void }) {
  const [value, setValue] = useState(initialValue || '');

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Chief Complaint</h2>
      <p className="text-sm text-slate-500">Describe the primary reason for the patient's visit today.</p>
      
      <div className="space-y-2">
        <Label htmlFor="complaint-description">Complaint Description</Label>
        <Textarea 
          id="complaint-description"
          placeholder="e.g. Patient presents with severe headache for 3 days..."
          value={value}
          onChange={(e) => setValue(e.target.value)}
          rows={5}
        />
      </div>

      <div className="flex justify-end pt-4">
        <Button onClick={() => onNext(value)} disabled={value.length < 5}>
          Next: Vitals
        </Button>
      </div>
    </div>
  );
}
