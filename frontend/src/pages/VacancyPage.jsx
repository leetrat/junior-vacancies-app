import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { analyzeVacancy } from '../api';
import './VacancyPage.css';

export default function VacancyPage() {
  const navigate = useNavigate();
  const [url,     setUrl]     = useState('');
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    if (!url.trim()) { setError('Введите ссылку на вакансию.'); return; }
    if (!url.includes('hh.ru/vacancy/')) {
      setError('Ссылка должна быть с hh.ru, например: https://hh.ru/vacancy/123456');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const data = await analyzeVacancy(url.trim());
      sessionStorage.setItem('vacancyResult', JSON.stringify(data));
      navigate('/vacancy/result');
    } catch (err) {
      const msg = err.response?.data?.error || 'Ошибка при анализе вакансии. Проверьте ссылку.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <div className="card tool-card">
          <div className="tool-icon-big">🔍</div>
          <h1 className="page-title">Анализ вакансии</h1>
          <p className="page-subtitle">
            Вставьте ссылку на вакансию с hh.ru — мы проверим её на красные флаги
            и покажем детальную информацию.
          </p>

          <form onSubmit={handleSubmit} className="tool-form">
            <label className="field-label">Ссылка на вакансию hh.ru</label>
            <input
              type="url"
              className="url-input"
              placeholder="https://hh.ru/vacancy/123456789"
              value={url}
              onChange={e => setUrl(e.target.value)}
              disabled={loading}
            />

            {error && <p className="error-msg">{error}</p>}

            <button className="btn-primary submit-btn" type="submit" disabled={loading}>
              {loading
                ? <><span className="spinner" /> Анализируем…</>
                : 'Проанализировать вакансию →'
              }
            </button>
          </form>

          <div className="tool-hint">
            <strong>Что мы проверяем:</strong> опыт работы vs. требования,
            зарплатные ловушки, признаки токсичной культуры, скрытые требования
            и другие красные флаги.
          </div>
        </div>
      </main>
    </div>
  );
}
