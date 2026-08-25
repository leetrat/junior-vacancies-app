import axios from 'axios';

const BASE = '/api';

/**
 * Отправляет форму опроса (multipart/form-data с возможным файлом резюме).
 * Возвращает: { clusterId, clusterName, clustersList, presetSkills,
 *               resumeUsed, skills, workFormats, salaryFrom, salaryTo }
 */
export async function submitSurvey(formData) {
  const res = await axios.post(`${BASE}/survey`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

/**
 * Получает список всех кластеров.
 */
export async function fetchClusters() {
  const res = await axios.get(`${BASE}/clusters`);
  return res.data;
}

/**
 * Запрашивает вакансии по выбранным кластерам + фильтрам.
 * Возвращает: { vacancies, total, minSalary, avgSalary,
 *               selectedClusterNames, skillFilters }
 */
export async function fetchResult(payload) {
  const res = await axios.post(`${BASE}/result`, payload);
  return res.data;
}

/**
 * Анализирует вакансию по ссылке hh.ru.
 * Возвращает: { vacancy, redFlagsText, redFlagsCount }
 */
export async function analyzeVacancy(vacancyUrl) {
  const res = await axios.post(`${BASE}/analyze_vacancy`, { vacancyUrl });
  return res.data;
}

/**
 * Анализирует резюме через LLM.
 * formData содержит: файл resume + поле career_field
 * Возвращает полный результат analyze_resume_hybrid()
 */
export async function analyzeResume(formData) {
  const res = await axios.post(`${BASE}/analyze_resume`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}