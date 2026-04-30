import { useQuery } from '@tanstack/react-query';
import { predictionsApi } from '@/api/predictions';
import { recommendationsApi } from '@/api/recommendations';
import { burdenApi } from '@/api/burden';
import { PredictionCard } from '@/components/visit/PredictionCard';
import { TestRecommendationList } from '@/components/visit/TestRecommendationList';
import { BurdenSummary } from '@/components/visit/BurdenSummary';
import { UncertaintyPanel } from '@/components/visit/UncertaintyPanel';
import { OverrideForm } from '@/components/visit/OverrideForm';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

interface ReviewStepProps {
  visitId: string;
}

export function ReviewStep({ visitId }: ReviewStepProps) {
  const navigate = useNavigate();
  const [showOverride, setShowOverride] = useState(false);

  const { data: predictionData, isLoading: pLoading } = useQuery({
    queryKey: ['predictions', visitId],
    queryFn: () => predictionsApi.getPrediction(visitId),
  });

  const { data: testsData, isLoading: tLoading } = useQuery({
    queryKey: ['tests', visitId],
    queryFn: () => recommendationsApi.getTests(visitId),
  });

  const { data: burdenData, isLoading: bLoading } = useQuery({
    queryKey: ['burden', visitId],
    queryFn: () => burdenApi.calculate(visitId),
  });

  if (pLoading || tLoading || bLoading) {
    return <div className="p-8 text-center text-slate-500">Generating AI Insights...</div>;
  }

  // Check for contradiction
  const uncertaintyFlags = Array.from(new Set([
    ...(predictionData?.uncertainty_flags || []),
    ...(burdenData?.uncertainty_flags || []),
  ]));
  const hasContradiction = uncertaintyFlags.some(f => f.toLowerCase().includes('contradict'));

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center border-b pb-4">
        <h2 className="text-2xl font-bold">Clinical AI Review</h2>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowOverride(!showOverride)}>
            {showOverride ? 'Hide Override Form' : 'Doctor Override'}
          </Button>
          <Button onClick={() => navigate(`/visits/${visitId}/report`)}>
            Generate Report
          </Button>
        </div>
      </div>

      {hasContradiction && (
         <div className="p-3 bg-red-100 text-red-700 rounded-md border border-red-300 font-bold">
            CONTRADICTORY SYMPTOMS DETECTED: Please review patient intake.
         </div>
      )}

      {/* Must render at TOP of screen per spec */}
      <UncertaintyPanel flags={uncertaintyFlags} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold mb-3">Differential Diagnosis</h3>
            {predictionData?.predictions.map((p, idx) => (
              <PredictionCard key={idx} prediction={p} />
            ))}
          </div>

          {burdenData && <BurdenSummary burden={burdenData} />}
        </div>

        <div>
          {testsData && <TestRecommendationList recommendations={testsData} />}
          
          {showOverride && (
            <OverrideForm visitId={visitId} onOverrideSubmitted={() => setShowOverride(false)} />
          )}
        </div>
      </div>
    </div>
  );
}
