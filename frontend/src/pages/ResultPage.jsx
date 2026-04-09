import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar      from '../components/Sidebar';
import VacancyCard  from '../components/VacancyCard';
import SkillFilter  from '../components/SkillFilter';
import { fetchResult } from '../api';
import './ResultPage.css';

const WORK_FORMAT_OPTIONS = [
  { value: 'remote',   label: '🏠 Удалённо' },
  { value: 'fullDay',  label: '🏢 Полный день' },
  { value: 'flexible', label: '🔄 Гибкий' },
  { value: 'shift',    label: '🔁 Сменный' },
];

const FLAG_LABELS = {
  green:  '✅ Без флагов',
  yellow: '⚠️ 1–2 флага',
  orange: '🟠 3–4 флага',
  red:    '🔴 5+ флагов',
};

export default function ResultPage() {
  const navigate = useNavigate();

  const [data,     setData]     = useState(null);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState('');

  // presetSkills храним в ref — не теряются при повторном fetchResult
  const presetSkillsRef = useRef([]);

  // Локальный фильтр по флагам (без запроса к бэку)
  const [filterFlag, setFilterFlag] = useState('all');

  // Фильтры с запросом к бэку
  const [selectedSkills, setSkills]      = useState(new Set());
  const [workFormats,    setWorkFormats] = useState([]);
  const [salaryFrom,     setSalaryFrom]  = useState('');
  const [salaryTo,       setSalaryTo]    = useState('');
  const basePayloadRef = useRef(null);

  // ── Первоначальная загрузка ───────────────────────────────────────────────
  useEffect(() => {
    const raw = sessionStorage.getItem('clusterSelection');
    if (!raw) { navigate('/'); return; }

    const selection = JSON.parse(raw);
    setWorkFormats(selection.workFormats || []);
    if (selection.salaryFrom) setSalaryFrom(String(selection.salaryFrom));
    if (selection.salaryTo)   setSalaryTo(String(selection.salaryTo));
    basePayloadRef.current = selection;

    fetchResult(selection)
      .then(res => {
        setData(res);
        // Сохраняем presetSkills в ref — они одинаковы для всех запросов
        if (res.presetSkills?.length) {
          presetSkillsRef.current = res.presetSkills;
        }
      })
      .catch(() => setError('Ошибка загрузки вакансий.'))
      .finally(() => setLoading(false));
  }, [navigate]);

  // ── Повторный запрос при применении фильтров ─────────────────────────────
  const applyFilters = useCallback(async () => {
    if (!basePayloadRef.current) return;
    setLoading(true);
    setError('');
    try {
      const payload = {
        ...basePayloadRef.current,
        skillFilters: [...selectedSkills],
        workFormats,
        salaryFrom: salaryFrom ? parseInt(salaryFrom) : null,
        salaryTo:   salaryTo   ? parseInt(salaryTo)   : null,
      };
      const res = await fetchResult(payload);
      setData(res);
      // presetSkills снова пришли — обновляем ref (они не изменятся, но на всякий случай)
      if (res.presetSkills?.length) presetSkillsRef.current = res.presetSkills;
    } catch {
      setError('Ошибка при применении фильтров.');
    } finally {
      setLoading(false);
    }
  }, [selectedSkills, workFormats, salaryFrom, salaryTo]);

  function toggleFormat(val) {
    setWorkFormats(prev =>
      prev.includes(val) ? prev.filter(v => v !== val) : [...prev, val]
    );
  }

  const vacancies = data?.vacancies || [];
  const filtered  = filterFlag === 'all'
    ? vacancies
    : vacancies.filter(v => v.flagColor === filterFlag);

  const plots = data?.plots || {};

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">

        {/* ── Заголовок ── */}
        <div className="card result-header">
          <h1 className="page-title">💼 Результаты подбора</h1>
          {data && (
            <p className="clusters-label">
              Кластеры: <strong>{data.selectedClusterNames?.join(', ')}</strong>
            </p>
          )}
        </div>

        {/* ── Фильтры ── */}
        <div className="card filters-panel">
          <h3 className="filters-title">🎛️ Фильтры</h3>

          {/* Навыки — presetSkills из ref, не теряются между запросами */}
          <SkillFilter
            presetSkills={presetSkillsRef.current}
            selectedSkills={selectedSkills}
            onChange={setSkills}
          />

          {/* Формат работы */}
          <div className="filter-row">
            <span className="filter-label">Формат:</span>
            <div className="chips-row">
              {WORK_FORMAT_OPTIONS.map(o => (
                <button
                  key={o.value}
                  className={`skill-chip ${workFormats.includes(o.value) ? 'selected' : ''}`}
                  onClick={() => toggleFormat(o.value)}
                >
                  {o.label}
                </button>
              ))}
            </div>
          </div>

          {/* Зарплата */}
          <div className="filter-row">
            <span className="filter-label">Зарплата (₽):</span>
            <div className="salary-inputs">
              <input
                type="number"
                placeholder="От"
                value={salaryFrom}
                onChange={e => setSalaryFrom(e.target.value)}
                min="0"
              />
              <span>—</span>
              <input
                type="number"
                placeholder="До"
                value={salaryTo}
                onChange={e => setSalaryTo(e.target.value)}
                min="0"
              />
            </div>
          </div>

          <button
            className="btn-primary apply-btn"
            onClick={applyFilters}
            disabled={loading}
          >
            {loading ? 'Загрузка…' : 'Применить фильтры'}
          </button>
        </div>

        {/* ── Статистика ── */}
        {data && (
          <div className="stats-row">
            <div className="stat-card">
              <span className="stat-value">{data.total}</span>
              <span className="stat-label">вакансий</span>
            </div>
            {data.minSalary && (
              <div className="stat-card">
                <span className="stat-value">от {data.minSalary.toLocaleString()} ₽</span>
                <span className="stat-label">мин. зарплата</span>
              </div>
            )}
            {data.avgSalary && (
              <div className="stat-card">
                <span className="stat-value">{data.avgSalary.toLocaleString()} ₽</span>
                <span className="stat-label">средняя зарплата</span>
              </div>
            )}
          </div>
        )}

        {/* ── Графики ── */}
        {data && (
          <div className="card plots-section">
            <h2 className="plots-title">📊 Аналитика кластера</h2>
            {data.plotsError && (
              <details style={{marginBottom:12}}>
                <summary style={{cursor:'pointer',color:'#e53e3e',fontSize:13}}>
                  ⚠️ Ошибка генерации графиков (нажмите для деталей)
                </summary>
                <pre style={{fontSize:11,background:'#fff5f5',padding:12,borderRadius:8,overflow:'auto',marginTop:8}}>
                  {data.plotsError}
                </pre>
              </details>
            )}
            {Object.keys(plots).length === 0 ? (
              <p className="plots-loading">
                {data.plotsError ? '❌ Графики недоступны из-за ошибки выше' : '⏳ Нет данных для графиков'}
              </p>
            ) : (
              <div className="plots-grid">
                {plots.flags_distribution_plot && (
                  <PlotCard title="Распределение red flags" src={plots.flags_distribution_plot} />
                )}
                {plots.top_skills_plot && (
                  <PlotCard title="Топ навыков" src={plots.top_skills_plot} />
                )}
                {plots.experience_distribution_plot && (
                  <PlotCard title="Распределение по опыту" src={plots.experience_distribution_plot} />
                )}
                {plots.top_red_flags_plot && (
                  <PlotCard title="Топ red flags" src={plots.top_red_flags_plot} />
                )}
              </div>
            )}
          </div>
        )}

        {/* ── Фильтр по уровню флагов ── */}
        <div className="card flag-filter-card">
          <div className="flag-filter-row">
            <button
              className={`flag-filter-btn ${filterFlag === 'all' ? 'active' : ''}`}
              onClick={() => setFilterFlag('all')}
            >
              Все ({vacancies.length})
            </button>
            {Object.entries(FLAG_LABELS).map(([color, label]) => {
              const count = vacancies.filter(v => v.flagColor === color).length;
              return (
                <button
                  key={color}
                  className={`flag-filter-btn flag-btn-${color} ${filterFlag === color ? 'active' : ''}`}
                  onClick={() => setFilterFlag(color)}
                >
                  {label} ({count})
                </button>
              );
            })}
          </div>
        </div>

        {/* ── Список вакансий ── */}
        {error && <p className="error-msg">{error}</p>}

        {loading
          ? <p className="loading-text">⏳ Загружаем вакансии…</p>
          : filtered.length === 0
            ? <p className="empty-msg">Вакансий не найдено. Попробуйте изменить фильтры.</p>
            : filtered.map(v => (
                <VacancyCard key={v.id || v.title + v.company} vacancy={v} />
              ))
        }

      </main>
    </div>
  );
}

function PlotCard({ title, src }) {
  return (
    <div className="plot-card">
      <p className="plot-title">{title}</p>
      <img src={`data:image/png;base64,${src}`} alt={title} className="plot-img" />
    </div>
  );
}
