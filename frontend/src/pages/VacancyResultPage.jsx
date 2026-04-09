import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import './VacancyResultPage.css';

export default function VacancyResultPage() {
  const navigate = useNavigate();
  const [result, setResult] = useState(null);

  useEffect(() => {
    const raw = sessionStorage.getItem('vacancyResult');
    if (!raw) { navigate('/vacancy'); return; }
    setResult(JSON.parse(raw));
  }, [navigate]);

  if (!result) return null;

  const { vacancy, redFlagsText, redFlagsCount } = result;
  const flagsList = redFlagsText
    ? redFlagsText.split(';').map(s => s.trim()).filter(Boolean)
    : [];

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">

        <div className="card vr-card">
          <div className="vr-header">
            <h1 className="vr-title">
              <a href={vacancy.alternate_url} target="_blank" rel="noreferrer">
                {vacancy.name}
              </a>
            </h1>
            <span className={`vr-flag-badge ${redFlagsCount === 0 ? 'safe' : redFlagsCount <= 2 ? 'warn' : 'danger'}`}>
              {redFlagsCount === 0 ? '✅ Чисто' : `⚠️ ${redFlagsCount} флаг(ов)`}
            </span>
          </div>

          <div className="vr-meta-grid">
            <MetaItem icon="🏢" label="Компания"     value={vacancy.employer_name} />
            <MetaItem icon="💰" label="Зарплата"     value={vacancy.salary} />
            <MetaItem icon="🕐" label="Опыт"         value={vacancy.experience} />
            <MetaItem icon="📍" label="Формат"       value={vacancy.work_format} />
          </div>

          {vacancy.skills_list?.length > 0 && (
            <div className="vr-skills-block">
              <p className="vr-block-title">Навыки</p>
              <div className="vr-skills">
                {vacancy.skills_list.map((s, i) => (
                  <span key={i} className="skill-tag">{s}</span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className={`card flags-card ${redFlagsCount === 0 ? 'flags-safe' : 'flags-danger'}`}>
          {redFlagsCount === 0 ? (
            <>
              <h2 className="flags-title safe">✅ Красных флагов не обнаружено</h2>
              <p className="flags-desc">
                Вакансия выглядит прозрачной и не содержит скрытых требований или подозрительных условий.
              </p>
            </>
          ) : (
            <>
              <h2 className="flags-title danger">⚠️ Обнаружено {redFlagsCount} красных флага(ов)</h2>
              <ul className="flags-list">
                {flagsList.map((flag, i) => (
                  <li key={i} className="flag-item">
                    <span className="flag-dot" />
                    {flag}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>

        <button className="btn-primary back-btn" onClick={() => navigate('/vacancy')}>
          ← Проанализировать другую вакансию
        </button>
      </main>
    </div>
  );
}

function MetaItem({ icon, label, value }) {
  return (
    <div className="meta-item">
      <span className="meta-icon">{icon}</span>
      <div>
        <p className="meta-label">{label}</p>
        <p className="meta-value">{value || '—'}</p>
      </div>
    </div>
  );
}
