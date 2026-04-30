import { expect, test } from '@playwright/test';

test('full patient visit flow reaches AI review', async ({ page }) => {
  await page.goto('/patients');

  await page.getByRole('link', { name: /add patient/i }).click();
  await page.getByLabel('Full Name').fill('E2E Patient Alpha');
  await page.getByLabel('Age').fill('54');
  await page.getByLabel('Gender').fill('female');
  await page.getByLabel('Phone Number').fill('555-0199');
  await page.getByLabel('Medical History').fill('Family history of diabetes');
  await page.getByRole('button', { name: /save patient/i }).click();

  await expect(page.getByRole('heading', { name: 'E2E Patient Alpha' })).toBeVisible();
  await page.getByRole('button', { name: /new visit/i }).click();

  await page.getByLabel('Complaint Description').fill('Fatigue with polyuria and polydipsia for two weeks');
  await page.getByRole('button', { name: /next: vitals/i }).click();

  await page.getByLabel(/heart rate/i).fill('92');
  await page.getByLabel(/respiratory rate/i).fill('18');
  await page.getByLabel(/temperature/i).fill('37');
  await page.getByLabel(/oxygen saturation/i).fill('98');
  await page.getByLabel(/systolic bp/i).fill('118');
  await page.getByLabel(/diastolic bp/i).fill('76');
  await page.getByRole('button', { name: /next: symptoms/i }).click();

  await page.getByText('Is the patient experiencing fatigue?').waitFor();
  await page.getByRole('button', { name: 'Yes' }).nth(0).click();
  await page.getByRole('button', { name: 'Yes' }).nth(1).click();
  await page.getByRole('button', { name: 'Yes' }).nth(2).click();
  await page.getByRole('button', { name: /submit intake/i }).click();

  await expect(page.getByRole('heading', { name: /clinical ai review/i })).toBeVisible();
  await expect(page.getByText('Differential Diagnosis')).toBeVisible();
  await expect(page.getByText('Recommended Tests')).toBeVisible();
  await expect(page.getByText('Financial Burden Analysis')).toBeVisible();
});
