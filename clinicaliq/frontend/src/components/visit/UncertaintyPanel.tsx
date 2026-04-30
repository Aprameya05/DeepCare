import { AlertTriangle } from 'lucide-react';

interface UncertaintyPanelProps {
  flags: string[];
}

export function UncertaintyPanel({ flags }: UncertaintyPanelProps) {
  if (!flags || flags.length === 0) return null;

  return (
    <div className="bg-amber-50 border-l-4 border-amber-500 p-4 mb-6 rounded-r-md">
      <div className="flex items-start">
        <AlertTriangle className="w-5 h-5 text-amber-500 mt-0.5 mr-3 shrink-0" />
        <div>
          <h3 className="text-amber-800 font-medium mb-1">Clinical Uncertainty Flags</h3>
          <ul className="list-disc list-inside text-sm text-amber-700 space-y-1">
            {flags.map((flag, idx) => (
              <li key={idx}>{flag}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
