export type CPOActionType = 'OrderTest' | 'Prescribe' | 'Refer' | 'Escalate' | 'Wait';
export type CurriculumLevel = 'simple' | 'moderate' | 'complex';

export interface CPORewardBreakdown {
  accuracy_gain: number;
  time_cost: number;
  financial_cost: number;
  burden: number;
}

export interface CPOAction {
  type: CPOActionType;
  detail: string;
  outcome?: string;
}

export interface CPOActionHistoryEntry {
  action: CPOAction;
  reward: number;
  reward_breakdown: CPORewardBreakdown;
}

export interface PatientScenarioInitialState {
  demographics: { age: number; sex: string; weight: number };
  vitals: { bp: string; hr: number; temp: number; spo2: number };
  symptoms: string[];
  labResults: Record<string, number | string>;
}

export interface PatientScenario {
  id: string;
  name: string;
  level: CurriculumLevel;
  initialState: PatientScenarioInitialState;
  groundTruthDiagnosis: string;
  optimalActionSequence: CPOActionType[];
  maxSteps: number;
  budgetCeiling: number;
  displayPriorResults: string;
}

export interface CPOState extends PatientScenarioInitialState {
  episodeId: string;
  stepCount: number;
  timeElapsed: number;
  costAccrued: number;
  actionHistory: CPOActionHistoryEntry[];
  maxSteps: number;
  budgetCeiling: number;
  diagnosisReached: boolean;
  currentAssessment: string;
}

export interface CPOStepResult {
  nextState: CPOState;
  reward: number;
  reward_breakdown: CPORewardBreakdown;
  done: boolean;
  diagnosisReached: boolean;
}

export interface CPORecommendation {
  action: CPOActionType;
  actionLabel: 'Order Test' | 'Prescribe' | 'Refer' | 'Escalate' | 'Wait';
  specific_detail: string;
  reasoning: string;
  reward_breakdown: CPORewardBreakdown;
}

const ACTION_BASE_COST: Record<CPOActionType, number> = {
  OrderTest: 150,
  Prescribe: 50,
  Refer: 200,
  Escalate: 1000,
  Wait: 0,
};

const ACTION_TIME_MINUTES: Record<CPOActionType, number> = {
  OrderTest: 60,
  Prescribe: 15,
  Refer: 120,
  Escalate: 30,
  Wait: 120,
};

const ACTION_BURDEN: Record<CPOActionType, number> = {
  OrderTest: -0.3,
  Prescribe: -0.1,
  Refer: -0.2,
  Escalate: -0.8,
  Wait: -0.05,
};

const ACTION_ACCURACY_GAIN: Record<CPOActionType, number> = {
  OrderTest: 0.45,
  Prescribe: 0.35,
  Refer: 0.3,
  Escalate: 0.5,
  Wait: 0.1,
};

function toActionLabel(action: CPOActionType): CPORecommendation['actionLabel'] {
  const labels: Record<CPOActionType, CPORecommendation['actionLabel']> = {
    OrderTest: 'Order Test',
    Prescribe: 'Prescribe',
    Refer: 'Refer',
    Escalate: 'Escalate',
    Wait: 'Wait',
  };
  return labels[action];
}

function calculateStepReward(action: CPOActionType): CPORewardBreakdown {
  return {
    accuracy_gain: Number(ACTION_ACCURACY_GAIN[action].toFixed(2)),
    time_cost: Number((-ACTION_TIME_MINUTES[action] / 300).toFixed(2)),
    financial_cost: Number((-ACTION_BASE_COST[action] / 1500).toFixed(2)),
    burden: Number(ACTION_BURDEN[action].toFixed(2)),
  };
}

export function totalReward(breakdown: CPORewardBreakdown): number {
  return Number(
    (breakdown.accuracy_gain + breakdown.time_cost + breakdown.financial_cost + breakdown.burden).toFixed(3)
  );
}

export class CPOEnv {
  private currentScenario: PatientScenario | null = null;
  private state: CPOState | null = null;

  reset(scenario: PatientScenario): CPOState {
    this.currentScenario = scenario;
    this.state = {
      ...scenario.initialState,
      episodeId: `${scenario.id}-${Date.now()}`,
      stepCount: 0,
      timeElapsed: 0,
      costAccrued: 0,
      actionHistory: [],
      maxSteps: scenario.maxSteps,
      budgetCeiling: scenario.budgetCeiling,
      diagnosisReached: false,
      currentAssessment: 'Initial triage. Awaiting first action.',
    };
    return this.state;
  }

  step(action: CPOAction): CPOStepResult {
    if (!this.state || !this.currentScenario) {
      throw new Error('Environment not initialized. Call reset() first.');
    }

    const rewardBreakdown = calculateStepReward(action.type);
    const reward = totalReward(rewardBreakdown);
    const nextStepCount = this.state.stepCount + 1;
    const expectedAction = this.currentScenario.optimalActionSequence[nextStepCount - 1];
    const actionMatchesPath = expectedAction ? expectedAction === action.type : false;
    const diagnosisReached =
      action.type === 'Escalate' ||
      (actionMatchesPath &&
        nextStepCount >= this.currentScenario.optimalActionSequence.length &&
        this.currentScenario.optimalActionSequence.length > 0);

    const nextState: CPOState = {
      ...this.state,
      stepCount: nextStepCount,
      timeElapsed: this.state.timeElapsed + ACTION_TIME_MINUTES[action.type],
      costAccrued: this.state.costAccrued + ACTION_BASE_COST[action.type],
      diagnosisReached,
      currentAssessment: diagnosisReached
        ? `Diagnosis aligned with pathway: ${this.currentScenario.groundTruthDiagnosis}`
        : actionMatchesPath
          ? 'Trajectory improving. Continue optimized pathway.'
          : 'Trajectory sub-optimal. Consider corrective action.',
      actionHistory: [
        ...this.state.actionHistory,
        {
          action,
          reward,
          reward_breakdown: rewardBreakdown,
        },
      ],
    };

    const done =
      diagnosisReached ||
      nextState.stepCount >= this.currentScenario.maxSteps ||
      nextState.costAccrued > this.currentScenario.budgetCeiling;

    this.state = nextState;
    return {
      nextState,
      reward,
      reward_breakdown: rewardBreakdown,
      done,
      diagnosisReached,
    };
  }
}

export function buildRecommendation(
  action: CPOActionType,
  detail: string,
  reasoning: string
): CPORecommendation {
  return {
    action,
    actionLabel: toActionLabel(action),
    specific_detail: detail,
    reasoning,
    reward_breakdown: calculateStepReward(action),
  };
}
