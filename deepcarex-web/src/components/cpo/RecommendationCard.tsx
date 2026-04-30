import { Activity, ShieldCheck, Microscope, AlertTriangle } from "lucide-react";
import type { RecommendationResult } from "../../types/cpoTypes";

interface RecommendationCardProps {
  result: Extract<RecommendationResult, { status: "recommend" }>;
}

export const RecommendationCard = ({ result }: RecommendationCardProps) => {
  const primaryTests = result.tests.filter((t) => t.priority === "primary");
  const secondaryTests = result.tests.filter((t) => t.priority === "secondary");
  const confidencePercent = Math.round(result.confidence * 100);

  return (
    <div className="glass-panel p-8 rounded-2xl border-t-4 border-biogreen shadow-[0_0_30px_rgba(0,255,136,0.1)] relative overflow-hidden">
      <div className="absolute top-0 right-0 p-6 opacity-10">
        <ShieldCheck className="w-48 h-48 text-biogreen" />
      </div>

      <div className="relative z-10">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-biogreen/20 rounded-xl">
            <Activity className="w-8 h-8 text-biogreen" />
          </div>
          <div>
            <h3 className="text-gray-400 uppercase tracking-widest text-sm font-mono">
              Primary Match
            </h3>
            <h2 className="text-3xl font-bold text-white">
              {result.condition.name}
            </h2>
          </div>
        </div>

        <p className="text-gray-300 text-lg leading-relaxed mb-8">
          {result.condition.rationale}
        </p>

        <div className="mb-8 bg-black/40 p-6 rounded-xl border border-white/5">
          <div className="flex justify-between items-end mb-2">
            <span className="text-sm font-mono text-gray-400">Match Confidence</span>
            <span className="text-2xl font-bold text-biogreen">
              {confidencePercent}%
            </span>
          </div>
          <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
            <div
              className="h-full bg-biogreen shadow-[0_0_10px_#00ff88]"
              style={{ width: `${confidencePercent}%` }}
            />
          </div>
        </div>

        <div className="space-y-6 mb-8">
          {primaryTests.length > 0 && (
            <div>
              <h4 className="flex items-center gap-2 text-biogreen font-semibold mb-4 border-b border-white/10 pb-2">
                <Microscope className="w-5 h-5" /> Recommended Primary Tests
              </h4>
              <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {primaryTests.map((test, idx) => (
                  <li
                    key={idx}
                    className="bg-white/5 px-4 py-3 rounded-lg border border-white/10 flex items-center gap-3"
                  >
                    <div className="w-2 h-2 rounded-full bg-biogreen" />
                    <span className="text-gray-200">{test.name}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {secondaryTests.length > 0 && (
            <div>
              <h4 className="text-gray-400 font-semibold mb-3">Consider Also</h4>
              <div className="flex flex-wrap gap-2">
                {secondaryTests.map((test, idx) => (
                  <span
                    key={idx}
                    className="bg-deepnavy border border-gray-700 text-gray-400 px-3 py-1.5 rounded-full text-sm"
                  >
                    {test.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="mt-8 p-4 bg-deepnavy/50 rounded-xl border border-white/5">
          <p className="text-xs text-gray-500 font-mono flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-yellow-500 shrink-0" />
            DISCLAIMER: This is a decision-support recommendation. Final clinical
            judgment rests with the treating physician.
          </p>
        </div>
      </div>
    </div>
  );
};
