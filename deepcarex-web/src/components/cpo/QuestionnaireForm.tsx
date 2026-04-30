import type { FormEvent } from "react";
import { Activity } from "lucide-react";
import type { QuestionnaireAnswers } from "../../types/cpoTypes";

export interface Question {
  id: string;
  label: string;
  type: "number" | "single_select" | "multi_select" | "scale_1_5" | "boolean";
  unit?: string;
  options?: string[];
  feature_key: string;
}

interface QuestionnaireFormProps {
  questions: Question[];
  answers: QuestionnaireAnswers;
  onAnswersChange: (answers: QuestionnaireAnswers) => void;
  onSubmit: () => void;
}

export const QuestionnaireForm = ({
  questions,
  answers,
  onAnswersChange,
  onSubmit,
}: QuestionnaireFormProps) => {
  const updateAnswer = (key: string, value: string | number | boolean | string[] | undefined) => {
    const nextAnswers = { ...answers };

    if (value === undefined) {
      delete nextAnswers[key];
    } else if (Array.isArray(value) && value.length === 0) {
      delete nextAnswers[key];
    } else if (typeof value === "string" && value.trim() === "") {
      delete nextAnswers[key];
    } else {
      nextAnswers[key] = value;
    }

    onAnswersChange(nextAnswers);
  };

  const handleChange = (key: string, value: string | number | boolean | string[]) => {
    updateAnswer(key, value);
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  const answeredCount = Object.values(answers).filter((value) => {
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === "string") return value.trim() !== "";
    return value !== undefined;
  }).length;
  const isSubmitDisabled = answeredCount < 5;

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      <div className="space-y-6">
        {questions.map((q) => (
          <div key={q.id} className="bg-white/5 p-6 rounded-xl border border-white/5 hover:border-cyan-400/30 transition-colors">
            <label className="block text-sm font-semibold text-gray-300 mb-4">
              {q.label}
            </label>

            {q.type === "boolean" && (
              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => handleChange(q.feature_key, true)}
                  className={`flex-1 py-3 px-4 rounded-lg border transition-colors ${
                    answers[q.feature_key] === true
                      ? "bg-cyan-400/20 border-cyan-400 text-cyan-400"
                      : "bg-deepnavy border-white/10 text-gray-400 hover:border-white/30"
                  }`}
                >
                  Yes
                </button>
                <button
                  type="button"
                  onClick={() => handleChange(q.feature_key, false)}
                  className={`flex-1 py-3 px-4 rounded-lg border transition-colors ${
                    answers[q.feature_key] === false
                      ? "bg-cyan-400/20 border-cyan-400 text-cyan-400"
                      : "bg-deepnavy border-white/10 text-gray-400 hover:border-white/30"
                  }`}
                >
                  No
                </button>
              </div>
            )}

            {q.type === "single_select" && q.options && (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {q.options.map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => handleChange(q.feature_key, opt)}
                    className={`py-2 px-4 rounded-lg border capitalize transition-colors text-sm ${
                      answers[q.feature_key] === opt
                        ? "bg-cyan-400/20 border-cyan-400 text-cyan-400"
                        : "bg-deepnavy border-white/10 text-gray-400 hover:border-white/30"
                    }`}
                  >
                    {opt.replace(/_/g, " ")}
                  </button>
                ))}
              </div>
            )}

            {q.type === "multi_select" && q.options && (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {q.options.map((opt) => {
                  const currentValues = (answers[q.feature_key] as string[]) || [];
                  const isSelected = currentValues.includes(opt);
                  return (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => {
                        let newValues;
                        if (isSelected) {
                          newValues = currentValues.filter((v) => v !== opt);
                        } else {
                          newValues = [...currentValues, opt];
                        }
                        updateAnswer(q.feature_key, newValues.length > 0 ? newValues : undefined);
                      }}
                      className={`py-2 px-4 rounded-lg border capitalize transition-colors text-sm ${
                        isSelected
                          ? "bg-cyan-400/20 border-cyan-400 text-cyan-400"
                          : "bg-deepnavy border-white/10 text-gray-400 hover:border-white/30"
                      }`}
                    >
                      {opt.replace(/_/g, " ")}
                    </button>
                  );
                })}
              </div>
            )}

            {q.type === "scale_1_5" && (
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((val) => (
                  <button
                    key={val}
                    type="button"
                    onClick={() => handleChange(q.feature_key, val)}
                    className={`flex-1 py-3 rounded-lg border transition-colors ${
                      answers[q.feature_key] === val
                        ? "bg-cyan-400/20 border-cyan-400 text-cyan-400"
                        : "bg-deepnavy border-white/10 text-gray-400 hover:border-white/30"
                    }`}
                  >
                    {val}
                  </button>
                ))}
              </div>
            )}

            {q.type === "number" && (
              <div className="relative">
                <input
                  type="number"
                  value={(answers[q.feature_key] as number) || ""}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val === "") {
                      updateAnswer(q.feature_key, undefined);
                    } else {
                      handleChange(q.feature_key, Number(val));
                    }
                  }}
                  className="w-full bg-deepnavy border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-400 transition-colors"
                  placeholder="Enter value..."
                />
                {q.unit && (
                  <div className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 font-mono text-sm pointer-events-none">
                    {q.unit}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="sticky bottom-6 flex flex-col items-center gap-4 bg-deepnavy/90 backdrop-blur-md p-6 rounded-2xl border border-cyan-400/20 shadow-[0_0_30px_rgba(0,0,0,0.5)] z-10">
        <div className="w-full flex items-center justify-between text-sm text-gray-400">
          <span>{answeredCount} questions answered</span>
          <span className={isSubmitDisabled ? "text-alertred" : "text-biogreen"}>
            {isSubmitDisabled ? `Need ${5 - answeredCount} more` : "Ready to analyze"}
          </span>
        </div>
        <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${
              isSubmitDisabled ? "bg-cyan-400" : "bg-biogreen"
            }`}
            style={{ width: `${Math.min(100, (answeredCount / 5) * 100)}%` }}
          />
        </div>
        <button
          type="submit"
          disabled={isSubmitDisabled}
          className="w-full relative inline-flex items-center justify-center px-8 py-4 font-bold text-deepnavy bg-cyan-400 rounded-lg overflow-hidden glass-panel-hover neon-box transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-biogreen"
        >
          Generate Recommendation <Activity className="w-5 h-5 ml-2" />
        </button>
      </div>
    </form>
  );
};
