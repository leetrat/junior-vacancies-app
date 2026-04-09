import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import { analyzeResume } from '../api';
import './ResumeAnalysisPage.css';

const FIELD_OPTIONS = [
  'Python-разработчик', 'Java-разработчик', 'Frontend-разработчик',
  'Data Scientist', 'Аналитик данных', 'DevOps-инженер',
  'QA-инженер', 'Мобильный разработчик', 'Fullstack-разработчик',
];

export default function ResumeAnalysisPage() {
  const [careerField, setCareerField] = useState('');
  const [resumeFile,  setResumeFile]  = useState(null);
  const [fileName,    setFileName]    = useState('');
  const [result,      setResult]      = useState(null);
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    if (!resumeFile) { setError('Загрузите файл резюме.'); return; }
    if (!careerField) { setError('Выберите специализацию.'); return; }
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('resume', resumeFile);
      fd.append('career_field', careerField);
      const data = await analyzeResume(fd);
      setResult(data);
    } catch {
      setError('Ошибка при анализе резюме. Попробуйте снова.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-content">

        <div className="page-header">
          <div>
            <h1>Анализ резюме</h1>
            <p>Загрузите резюме для получения рекомендаций по улучшению</p>
          </div>
        </div>

        <div className="content-card ra-form-card">
          <form onSubmit={handleSubmit}>
            <div className="ra-form-group">
              <label>Целевая специализация:</label>
              <select value={careerField} onChange={e => setCareerField(e.target.value)} required>
                <option value="">Выберите специализацию…</option>
                {FIELD_OPTIONS.map(f => <option key={f} value={f}>{f}</option>)}
              </select>
            </div>

            <div className="ra-form-group">
              <label>Файл резюме (PDF или DOCX):</label>
              <label className="resume-upload">
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={e => {
                    const f = e.target.files[0];
                    setResumeFile(f || null);
                    setFileName(f ? f.name : '');
                  }}
                />
                <span>{fileName ? `✅ ${fileName}` : ' Выбрать файл'}</span>
              </label>
            </div>

            {error && <p className="error-msg">{error}</p>}
            <button type="submit" className="submit-btn" disabled={loading}>
              {loading ? 'Анализируем…' : 'Проанализировать резюме'}
            </button>
          </form>
        </div>

        {result && (
          <>
            <div className="content-card ra-section">
              <h3>Общая оценка</h3>
              <p><strong>Целевая область:</strong> {result.target_field}</p>
              <p><strong>Предварительный уровень:</strong> {result.pre_level} ({result.pre_score}/100)</p>
              <p><strong>Опыт работы:</strong> {result.experience_years} {declYears(result.experience_years)}</p>
              <p><strong>Образование:</strong> {result.has_education ? 'Присутствует' : 'Отсутствует'}</p>
              <p><strong>Пет-проекты:</strong> {result.project_count}</p>
              <p><strong>GitHub:</strong> {result.has_github ? '✅ Есть' : '❌ Не найден'}</p>

              {result.all_skills?.length > 0 && (
                <>
                  <h3 style={{marginTop:'16px'}}>Извлечённые навыки</h3>
                  <div className="ra-skills">
                    {result.all_skills.map(s => <span key={s} className="skill-tag">{s}</span>)}
                  </div>
                </>
              )}

              {result.strengths?.length > 0 && (
                <>
                  <h3 style={{marginTop:'16px'}}>Сильные стороны</h3>
                  <ul className="ra-list">
                    {result.strengths.map((s, i) => <li key={i}>{s}</li>)}
                  </ul>
                </>
              )}
            </div>

            <div className="content-card ra-recommendations">
              <h3>Рекомендации для роста</h3>
              {result.gaps?.length > 0 ? (
                <ul className="ra-list">
                  {result.gaps.map((g, i) => <li key={i}>Добавьте {g}</li>)}
                </ul>
              ) : (
                <p>Ваше резюме выглядит отлично!</p>
              )}
              {result.portfolio_recommendation && (
                <p style={{marginTop:'12px', color:'#4a5568'}}>
                  💼 {result.portfolio_recommendation}
                </p>
              )}
            </div>

            {result.hr_comment && (
              <div className="content-card ra-comment">
                <p><strong>Комментарий HR:</strong> {result.hr_comment}</p>
                {result.fun_motivation && (
                  <p style={{marginTop:'10px', fontStyle:'italic', color:'#856404'}}>
                    {result.fun_motivation}
                  </p>
                )}
              </div>
            )}
          </>
        )}

        {!result && !loading && (
          <div className="content-card">
            <div className="placeholder-content">
              <div className="placeholder-icon">📄</div>
              <h3>Загрузите ваше резюме</h3>
              <p>Система оценит сильные стороны, выявит зоны роста и даст рекомендации по улучшению вашего резюме.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function declYears(n) {
  if (n % 100 >= 11 && n % 100 <= 14) return 'лет';
  switch (n % 10) {
    case 1: return 'год';
    case 2: case 3: case 4: return 'года';
    default: return 'лет';
  }
}
