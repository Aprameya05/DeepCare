import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronUp, BookOpen } from 'lucide-react';

interface PredictionCardProps {
  prediction: {
    disease: string;
    confidence: number;
    pubmed_evidence: string[];
  };
}

export function PredictionCard({ prediction }: PredictionCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card className="mb-4">
      <CardContent className="p-4">
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-semibold text-lg">{prediction.disease}</h3>
          <span className="font-bold text-blue-600">{prediction.confidence}% Match</span>
        </div>
        
        {/* Confidence Bar */}
        <div className="w-full bg-slate-200 rounded-full h-2.5 dark:bg-slate-700 mb-4">
          <div 
            className="bg-blue-600 h-2.5 rounded-full" 
            style={{ width: `${prediction.confidence}%` }}
          ></div>
        </div>

        {/* Pubmed references expandable */}
        {prediction.pubmed_evidence && prediction.pubmed_evidence.length > 0 && (
          <div>
            <Button 
              variant="ghost" 
              size="sm" 
              className="px-0 text-slate-500 hover:text-slate-800"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? <ChevronUp className="w-4 h-4 mr-1" /> : <ChevronDown className="w-4 h-4 mr-1" />}
              {prediction.pubmed_evidence.length} PubMed References
            </Button>
            
            {expanded && (
              <div className="mt-2 space-y-2 bg-slate-50 dark:bg-slate-900 p-3 rounded-md">
                {prediction.pubmed_evidence.map((ref, idx) => (
                  <div key={idx} className="flex gap-2 text-sm">
                    <BookOpen className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
                    <a href={ref} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline break-all">
                      {ref}
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
