import { expect, test } from '@playwright/test';

const api = 'http://127.0.0.1:8000/api/v1';

test('uncertainty flags are shown at the top of the review', async ({ page, request }) => {
  const patient = await request.post(`${api}/patients/`, {
    data: {
      name: 'E2E Patient Uncertainty',
      age: 67,
      gender: 'male',
      phone: '555-0200',
      medical_history: '',
    },
  });
  const patientId = (await patient.json()).id;

  const visit = await request.post(`${api}/visits/`, {
    data: {
      patient_id: patientId,
      chief_complaint: 'Fever with cough',
    },
  });
  const visitId = (await visit.json()).id;

  await request.post(`${api}/vitals/`, {
    data: {
      visit_id: visitId,
      heart_rate: 132,
    },
  });
  await request.post(`${api}/visits/${visitId}/symptoms`, {
    data: {
      fever: true,
      cough: true,
      notes: 'denies fever',
    },
  });

  await page.goto(`/visits/${visitId}`);

  await expect(page.getByText('Clinical Uncertainty Flags')).toBeVisible();
  await expect(page.getByText('CONFLICTING_SYMPTOMS')).toBeVisible();
  await expect(page.getByText('MISSING_CRITICAL_VITALS')).toBeVisible();
  await expect(page.getByText('OUT_OF_RANGE_VITALS')).toBeVisible();
});
