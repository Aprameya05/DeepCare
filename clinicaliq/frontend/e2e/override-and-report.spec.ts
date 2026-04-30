import { expect, test } from '@playwright/test';

const api = 'http://127.0.0.1:8000/api/v1';

test('doctor override can be submitted and report can be generated', async ({ page, request }) => {
  const patient = await request.post(`${api}/patients/`, {
    data: {
      name: 'E2E Patient Report',
      age: 49,
      gender: 'female',
      phone: '555-0201',
      medical_history: 'Prediabetes',
    },
  });
  const patientId = (await patient.json()).id;

  const visit = await request.post(`${api}/visits/`, {
    data: {
      patient_id: patientId,
      chief_complaint: 'Fatigue, polyuria, polydipsia',
    },
  });
  const visitId = (await visit.json()).id;

  await request.post(`${api}/vitals/`, {
    data: {
      visit_id: visitId,
      heart_rate: 88,
      respiratory_rate: 16,
      temperature: 36.8,
      oxygen_saturation: 99,
      systolic_bp: 116,
      diastolic_bp: 74,
    },
  });
  await request.post(`${api}/visits/${visitId}/symptoms`, {
    data: {
      fatigue: true,
      polyuria: true,
      polydipsia: true,
    },
  });

  await page.goto(`/visits/${visitId}`);
  await expect(page.getByRole('heading', { name: /clinical ai review/i })).toBeVisible();

  await page.getByRole('button', { name: /doctor override/i }).click();
  await page.getByLabel(/alternative diagnosis/i).fill('diabetes');
  await page.getByLabel(/reason for override/i).fill('Clinician confirmed diabetes after reviewing intake.');
  await page.getByRole('button', { name: /submit override/i }).click();

  await expect(page.getByText('Doctor Override (Optional)')).toBeHidden();
  await page.getByRole('button', { name: /generate report/i }).click();

  await expect(page.getByRole('heading', { name: /clinical report/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /download pdf/i })).toBeEnabled();
  await expect(page.locator('iframe[title="PDF Preview"]')).toHaveAttribute('src', `/api/v1/reports/${visitId}`);
});
