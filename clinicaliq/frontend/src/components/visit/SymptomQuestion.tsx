import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface SymptomQuestionProps {
  question: {
    id: string;
    text: string;
    type: 'boolean' | 'scale' | 'text';
    options?: string[];
  };
  value: any;
  onChange: (value: any) => void;
}

export function SymptomQuestion({ question, value, onChange }: SymptomQuestionProps) {
  return (
    <div className="p-4 border rounded-lg bg-white dark:bg-slate-950 shadow-sm space-y-3">
      <Label className="text-base font-medium">{question.text}</Label>
      
      {question.type === 'boolean' && (
        <div className="flex gap-2 mt-2">
          <Button
            type="button"
            variant={value === true ? 'default' : 'outline'}
            onClick={() => onChange(true)}
            className="w-24"
          >
            Yes
          </Button>
          <Button
            type="button"
            variant={value === false ? 'default' : 'outline'}
            onClick={() => onChange(false)}
            className="w-24"
          >
            No
          </Button>
        </div>
      )}

      {question.type === 'scale' && (
        <div className="flex gap-1 mt-2 flex-wrap">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
            <Button
              key={num}
              type="button"
              variant={value === num ? 'default' : 'outline'}
              onClick={() => onChange(num)}
              className="w-10 h-10 p-0"
            >
              {num}
            </Button>
          ))}
        </div>
      )}

      {question.type === 'text' && (
        <div className="mt-2">
          <Input
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Please describe..."
          />
        </div>
      )}
    </div>
  );
}
