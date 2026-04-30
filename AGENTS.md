# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

**DeepCareX** is a medical AI diagnostic platform with two distinct parts:

1. **`deepcarex-web/`** — The active React/TypeScript frontend. This is the primary codebase for ongoing development. It uses Google's Gemini API as the AI inference engine (not local ML models).
2. **`Models/` and `Datasets/`** — Saved deep learning models (`.hdf`, `.h5`, `.pkl`) and datasets for 8 diseases. These were used in the original Flask backend (now superseded by the web frontend).
3. **`Dockerfile`** — Docker config for the legacy Flask backend (references a `Website/` directory that is no longer in this repo).

## Frontend Development Commands

All commands run from `deepcarex-web/`:

```bash
cd deepcarex-web
npm install        # Install dependencies
npm run dev        # Start dev server (Vite)
npm run build      # TypeScript check + Vite build
npm run preview    # Preview production build
```

## Architecture: `deepcarex-web/`

The frontend is a Vite + React 19 + TypeScript SPA styled with Tailwind CSS.

**Routing** (`src/App.tsx`):
- `/` → `Home` — landing page
- `/dashboard` → `Dashboard` — disease module selection grid
- `/diagnosis/:diseaseId` → `DiagnosisForm` — input form for a selected disease
- `/result` → `Result` — diagnosis output (receives state via `navigate`)
- `/about`, `/contact` → static pages
- `/cpo` → `CPO` — Clinical Pathway Optimizer (reinforcement-learning-style decision tool)

**AI Layer** (`src/services/gemini.ts`):
- All AI inference goes through the Google Gemini API (`gemini-1.5-pro`).
- Three exported functions: `runImageDiagnosis`, `runParameterDiagnosis`, `runCPOPathway`.
- Falls back to a mock/simulated response if the API call fails (quota exhaustion, missing key).
- The Gemini API key is loaded from `VITE_GEMINI_API_KEY` env var or from `localStorage` (user-entered at runtime).

**Disease Modules** (defined inline in `src/pages/DiagnosisForm.tsx` as `DISEASE_CONFIGS`):
- **Image-based** (MRI/X-Ray/CT): Alzheimer's, Brain Tumor, COVID-19, Pneumonia, Kidney Disease
- **Parameter-based** (clinical inputs): Breast Cancer, Diabetes, Hepatitis C
- Route param `diseaseId` (e.g., `alzheimers`, `brain_tumor`, `covid`) selects the config.

**Design System** (Tailwind custom theme in `tailwind.config.js`):
- `bg-deepnavy` (`#0a0f1e`) — primary dark background
- `cyan-400` (`#00d4ff`) — neon cyan accent
- `biogreen` (`#00ff88`) — green highlight
- `alertred` (`#ff4d6d`) — error/alert color
- CSS classes `glass-panel`, `neon-text`, `neon-box`, `scan-line` are defined in `src/index.css`

**Key dependencies**: `framer-motion` (animations), `react-router-dom` v7, `@tsparticles/react` (particle background), `lucide-react` (icons).

## Environment Variables

Create `deepcarex-web/.env` for local development:

```
VITE_GEMINI_API_KEY=your_gemini_api_key_here
```

Without this, users are prompted to enter their key at runtime (stored in `localStorage`).

## CPO Environment Architecture

```
deepcarex-web/src/
├── data/
│   └── scenarioGenerator.ts   ← 7 EHR scenarios (3 levels, MIMIC-IV priors)
│       exports: PatientScenario, CPOActionType, generateScenario(), getCurriculumScenarios()
├── env/
│   └── CPOEnv.ts              ← OpenEnv-style RL environment
│       CPOEnv.reset(scenario?) → CPOState
│       CPOEnv.step(action)    → { nextState, reward, done, info }
│       CPOEnv.render()        → CPOStateSnapshot
│       CPOEnv.getCurriculumScenarios(level)
├── services/
│   └── gemini.ts              ← AI layer (runCPOPathway accepts CPOState)
└── pages/
    └── CPO.tsx                ← UI: wires CPOEnv + Gemini, shows Δr per step

Data flow per turn:
  CPO.tsx → env.reset(scenario) → CPOState
  CPO.tsx → gemini.runCPOPathway(state, cumR) → CPOActionResponse
  user provides outcome
  CPO.tsx → env.step({type, detail, outcome}) → {nextState, reward, done}
  repeat until done
```

### Reward Function

```
R_step = accuracy_delta - 0.3 × norm_time - 0.3 × norm_cost - 0.4 × burden

accuracy_delta : 0.20 if action matches optimal sequence, else 0.05
norm_time      : timeElapsed / (maxSteps × 120 min)
norm_cost      : costAccrued / budgetCeiling
burden         : OrderTest 0.3 | Prescribe 0.1 | Refer 0.2 | Escalate 0.8 | Wait 0.05
```

### Scenario Curriculum

| Level    | ID              | Condition                          | Max Steps | Budget |
|----------|-----------------|-------------------------------------|-----------|--------|
| simple   | uti             | Uncomplicated UTI                  | 5         | $600   |
| simple   | pneumonia       | Community-Acquired Pneumonia        | 6         | $800   |
| simple   | htn_crisis      | Hypertensive Crisis                 | 6         | $700   |
| moderate | t2dm_aki        | T2DM + AKI                         | 8         | $1500  |
| moderate | chf_pneumonia   | Acute CHF exacerbation + CAP        | 8         | $2000  |
| complex  | sepsis_mof      | Septic Shock + MODS                 | 4         | $5000  |
| complex  | polytrauma      | Polytrauma (MVC)                    | 3         | $5000  |

### Run Commands (CPO demo on port 3001)

```bash
# Dev
cd deepcarex-web && npm run dev

# Docker (exposes port 3001)
docker compose up --build
```

## Git Safety

- Never push to any remote automatically.
- Only run `git push` when the user explicitly asks for it.
