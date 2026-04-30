import { AlertCircle, ChevronRight, UserPlus } from "lucide-react";
import type { RecommendationResult } from "../../types/cpoTypes";

interface EscalationCardProps {
  result: Extract<RecommendationResult, { status: "escalate" }>;
}

export const EscalationCard = ({ result }: EscalationCardProps) => {
  const isBelowThreshold = result.reason === "below_threshold";
  const reasonText =
    result.reason === "no_match"
      ? "No clear pattern matched"
      : result.reason === "below_threshold"
      ? "Ambiguous symptom pattern"
      : "Insufficient data provided";

  return (
    <div className="glass-panel p-8 rounded-2xl border-t-4 border-yellow-500 shadow-[0_0_30px_rgba(234,179,8,0.1)] relative overflow-hidden">
      <div className="absolute top-0 right-0 p-6 opacity-10">
        <AlertCircle className="w-48 h-48 text-yellow-500" />
      </div>

      <div className="relative z-10">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-yellow-500/20 rounded-xl">
            <AlertCircle className="w-8 h-8 text-yellow-500" />
          </div>
          <div>
            <h3 className="text-gray-400 uppercase tracking-widest text-sm font-mono">
              Clinical Escalation Required
            </h3>
            <h2 className="text-3xl font-bold text-white">{reasonText}</h2>
          </div>
        </div>

        <p className="text-gray-300 text-lg leading-relaxed mb-8 bg-yellow-500/10 p-5 rounded-xl border border-yellow-500/20">
          {result.message}
        </p>

        {isBelowThreshold && result.topCandidates && result.topCandidates.length > 0 && (
          <div className="mb-8">
            <h4 className="text-gray-400 font-semibold mb-4 border-b border-white/10 pb-2">
              Closest Considered Conditions
            </h4>
            <div className="space-y-3">
              {result.topCandidates.map((candidate, idx) => {
                const confPercent = Math.round(candidate.confidence * 100);
                return (
                  <div
                    key={idx}
                    className="bg-black/40 border border-white/5 rounded-lg p-4 flex justify-between items-center"
                  >
                    <span className="text-gray-200">{candidate.condition_name}</span>
                    <div className="flex items-center gap-3">
                      <div className="w-24 bg-gray-800 h-1.5 rounded-full overflow-hidden hidden sm:block">
                        <div
                          className="h-full bg-yellow-500"
                          style={{ width: `${confPercent}%` }}
                        />
                      </div>
                      <span className="text-sm font-mono text-yellow-500">
                        {confPercent}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="mt-8 flex justify-center">
          <div className="flex items-center gap-3 bg-yellow-500/10 text-yellow-500 px-6 py-4 rounded-xl border border-yellow-500/30">
            <UserPlus className="w-6 h-6" />
            <span className="font-semibold text-lg">Consult a clinician for further evaluation</span>
            <ChevronRight className="w-5 h-5 ml-2 opacity-70" />
          </div>
        </div>
      </div>
    </div>
  );
};
