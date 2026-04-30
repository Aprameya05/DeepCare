export interface VitalRange {
  min: number;
  max: number;
  label: string;
}

export const vitalRanges: Record<string, VitalRange> = {
  heart_rate: { min: 60, max: 100, label: 'bpm' },
  respiratory_rate: { min: 12, max: 20, label: 'breaths/min' },
  temperature: { min: 36.1, max: 37.2, label: '°C' },
  oxygen_saturation: { min: 95, max: 100, label: '%' },
  systolic_bp: { min: 90, max: 120, label: 'mmHg' },
  diastolic_bp: { min: 60, max: 80, label: 'mmHg' }
};

export function isAbnormal(vital: string, value: number): boolean {
  const range = vitalRanges[vital];
  if (!range) return false;
  return value < range.min || value > range.max;
}
