import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, RotateCcw, Stethoscope } from "lucide-react";
import { useNavigate } from "react-router-dom";

import questionnaireData from "../data/cpoQuestionnaire.json";
import casesData from "../data/cpoClinicalCases.json";
import { recommendTests } from "../services/cpoEngine";
import type { QuestionnaireAnswers, RecommendationResult, ClinicalCase } from "../types/cpoTypes";

import { QuestionnaireForm } from "../components/cpo/QuestionnaireForm";
import { RecommendationCard } from "../components/cpo/RecommendationCard";
import { EscalationCard } from "../components/cpo/EscalationCard";
import type { Question } from "../components/cpo/QuestionnaireForm";

const questions = questionnaireData.questions as Question[];
const cases = casesData.cases as ClinicalCase[];

export const CPOTriage = () => {
  const navigate = useNavigate();
  const [view, setView] = useState<"form" | "result">("form");
  const [result, setResult] = useState<RecommendationResult | null>(null);

  const handleSubmit = (answers: QuestionnaireAnswers) => {
    const outcome = recommendTests(answers, cases);
    setResult(outcome);
    setView("result");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleStartOver = () => {
    setView("form");
    setResult(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="min-h-screen pt-24 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto pb-20">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center text-cyan-400 hover:text-biogreen mb-8 transition-colors"
      >
        <ArrowLeft className="w-5 h-5 mr-2" /> Back
      </button>

      <div className="mb-8 text-center">
        <div className="inline-flex items-center justify-center p-4 bg-cyan-400/10 rounded-full mb-4 border border-cyan-400/20 shadow-[0_0_20px_rgba(0,212,255,0.15)]">
          <Stethoscope className="w-10 h-10 text-cyan-400" />
        </div>
        <h1 className="text-4xl font-bold text-white mb-3">Clinical Pathway Optimizer</h1>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
          Decision-support triage tool for recommending diagnostic tests based on symptom profiles.
        </p>
      </div>

      <AnimatePresence mode="wait">
        {view === "form" && (
          <motion.div
            key="form"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="glass-panel p-8 rounded-2xl border border-cyan-400/20 shadow-[0_0_30px_rgba(0,0,0,0.3)] relative"
          >
            <span className="absolute top-0 right-0 p-4 font-mono text-xs text-white/30 uppercase tracking-widest">
              TRIAGE QUESTIONNAIRE
            </span>
            <QuestionnaireForm questions={questions} onSubmit={handleSubmit} />
          </motion.div>
        )}

        {view === "result" && result && (
          <motion.div
            key="result"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="space-y-6"
          >
            {result.status === "recommend" ? (
              <RecommendationCard result={result} />
            ) : (
              <EscalationCard result={result} />
            )}

            <div className="flex justify-center mt-8">
              <button
                onClick={handleStartOver}
                className="flex items-center px-6 py-3 bg-white/5 hover:bg-white/10 text-cyan-400 rounded-xl border border-white/10 transition-colors"
              >
                <RotateCcw className="w-5 h-5 mr-2" /> Start New Assessment
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
