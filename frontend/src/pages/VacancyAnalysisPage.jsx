import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import { analyzeVacancy } from '../api';
import './VacancyAnalysisPage.css';

export default function VacancyAnalysisPage() {
  const [url,     setUrl]     = useState('');
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('vacancy_url', url);
      const data = await analyzeVacancy(fd);
      setResult(data);
    } catch {
      setError('Ошибка при анализе вакансии. Проверьте ссылку и попробуйте снова.');
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
            <h1>Анализ вакансии</h1>
            <p>Вставьте ссылку на вакансию с hh.ru, чтобы получить детальный анализ</p>
          </div>
        </div>

        <div className="content-card va-form-card">
          <form onSubmit={handleSubmit}>
            <div className="va-form-group">
              <label htmlFor="vacancy_url">Ссылка на вакансию HH.ru:</label>
              <input
                id="vacancy_url"
                type="text"
                value={url}
                onChange={e => setUrl(e.target.value)}
                placeholder="Например: https://hh.ru/vacancy/123456789"
                required
              />
            </div>
            {error && <p className="error-msg">{error}</p>}
            <button type="submit" className="submit-btn" disabled={loading}>
              {loading ? 'Анализируем…' : 'Анализировать вакансию'}
            </button>
          </form>
        </div>
        {result && (
          <>
            <div className="content-card va-details">
              <h3>
                <a href={result.vacancy.alternate_url} target="_blank" rel="noreferrer">
                  {result.vacancy.name}
                </a>
              </h3>
              <p><strong>Компания:</strong> {result.vacancy.employer_name}</p>
              <p><strong>Зарплата:</strong> {result.vacancy.salary}</p>
              <p><strong>Опыт:</strong> {result.vacancy.experience}</p>
              <p><strong>Формат работы:</strong> {result.vacancy.work_format}</p>
              {result.vacancy.skills_list?.length > 0 && (
                <p>
                  <strong>Навыки:</strong>{' '}
                  <span className="va-skills">
                    {result.vacancy.skills_list.map(s => (
                      <span key={s} className="skill-tag">{s}</span>
                    ))}
                  </span>
                </p>
              )}
            </div>

            <div className={`content-card va-flags ${result.redFlagsCount === 0 ? 'safe' : 'danger'}`}>
              {result.redFlagsCount > 0 ? (
                <>
                  <h3>⚠️ Обнаружено {result.redFlagsCount} красных флага(ов):</h3>
                  <ul>
                    {result.redFlagsText.split(';').filter(Boolean).map((flag, i) => (
                      <li key={i}>{flag.trim()}</li>
                    ))}
                  </ul>
                </>
              ) : (
                <>
                  <h3>✓ Красных флагов не обнаружено!</h3>
                  <p>Эта вакансия выглядит прозрачной и не содержит скрытых требований или подозрительных условий.</p>
                </>
              )}
            </div>
          </>
        )}

        {!result && !loading && (
          <div className="content-card">
            <div className="placeholder-content">
              <div className="placeholder-icon">🔍</div>
              <h3>Скоро здесь будет анализ</h3>
              <p>Загрузите описание вакансии или вставьте ссылку, чтобы получить подробный анализ требований, ключевых навыков и соответствия вашему профилю.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
