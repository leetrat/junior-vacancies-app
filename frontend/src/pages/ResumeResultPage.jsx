import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import './ResumeResultPage.css';

const LEVEL_COLORS = {
  Trainee: { bg: '#ebf8ff', border: '#90cdf4', text: '#2b6cb0' },
  Junior:  { bg: '#f0fff4', border: '#9ae6b4', text: '#276749' },
  Middle:  { bg: '#fffff0', border: '#faf089', text: '#7b6010' },
  Senior:  { bg: '#fff5f5', border: '#fc8181', text: '#c53030' },
};

export default function ResumeResultPage() {
  const navigate = useNavigate();
  const [result, setResult] = useState(null);

  useEffect(() => {
    const raw = sessionStorage.getItem('resumeResult');
    if (!raw) { navigate('/resume'); return; }
    setResult(JSON.parse(raw));
  }, [navigate]);

  if (!result) return null;

  const {
    target_field, level, level_score, experience_years,
    has_experience, has_education, extracted_skills,
    strengths, gaps, project_count, recommendations,
    hr_comment, fun_motivation, llm_available,
  } = result;

  const lvlStyle = LEVEL_COLORS[level] || LEVEL_COLORS.Junior;

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">

        <div className="card rr-header" style={{ borderLeft: `4px solid ${lvlStyle.border}`, background: lvlStyle.bg }}>
          <div className="rr-level-row">
            <div>
              <p className="rr-field">Специализация: <strong>{target_field}</strong></p>
              <h1 className="rr-level" style={{ color: lvlStyle.text }}>{level}</h1>
              <p className="rr-score">{level_score} / 100 баллов</p>
            </div>
            <div className="rr-score-circle" style={{ borderColor: lvlStyle.border, color: lvlStyle.text }}>
              {level_score}
            </div>
          </div>

          <div className="rr-meta-row">
            <MetaBadge icon="🕐" label={`Опыт: ${has_experience ? `${experience_years} лет` : 'нет'}`} />
            <MetaBadge icon="🎓" label={`Образование: ${has_education ? 'есть' : 'нет'}`} />
            <MetaBadge icon="💼" label={`Pet-проектов: ${project_count}`} />
          </div>
        </div>

        <div className="rr-two-col">

          <div className="card rr-section rr-strengths">
            <h2 className="rr-section-title">✅ Сильные стороны</h2>
            {strengths.length > 0 ? (
              <div className="skill-chips">
                {strengths.map(s => <span key={s} className="skill-chip-green">{s}</span>)}
              </div>
            ) : (
              <p className="rr-empty">Нет навыков, релевантных для выбранной специализации</p>
            )}

            {extracted_skills.length > 0 && (
              <>
                <h3 className="rr-sub-title">Все найденные навыки</h3>
                <div className="skill-chips">
                  {extracted_skills.map(s => <span key={s} className="skill-chip-neutral">{s}</span>)}
                </div>
              </>
            )}
          </div>

          <div className="card rr-section rr-gaps">
            <h2 className="rr-section-title">📈 Что развить</h2>
            {gaps.length > 0 ? (
              <ul className="rr-list rr-gaps-list">
                {gaps.map(g => <li key={g}><span className="gap-dot"/>Нужен: <strong>{g}</strong></li>)}
              </ul>
            ) : (
              <p className="rr-empty">Все ключевые навыки специализации присутствуют!</p>
            )}
          </div>
        </div>

        {recommendations.length > 0 && (
          <div className="card rr-section rr-recommendations">
            <h2 className="rr-section-title">🗺️ Рекомендации</h2>
            <ol className="rr-list rr-rec-list">
              {recommendations.map((r, i) => <li key={i}>{r}</li>)}
            </ol>
          </div>
        )}

        {llm_available && (
          <>
            {hr_comment && (
              <div className="card rr-llm-block rr-hr-comment">
                <h2 className="rr-section-title">💬 Комментарий HR-консультанта</h2>
                <p className="rr-llm-text">{hr_comment}</p>
              </div>
            )}

            {fun_motivation && (
              <div className="card rr-llm-block rr-motivation">
                <h2 className="rr-section-title">🎉 Мотивация дня</h2>
                <p className="rr-llm-text rr-motivation-text">{fun_motivation}</p>
              </div>
            )}
          </>
        )}

        {!llm_available && (
          <div className="card rr-no-llm">
            <p>
              ⚠️ AI-комментарий недоступен — модель не найдена или не загружена.
              Положите файл <code>model.gguf</code> в папку <code>backend/data/</code>.
            </p>
          </div>
        )}

        <button className="btn-primary back-btn" onClick={() => navigate('/resume')}>
          ← Проанализировать другое резюме
        </button>

      </main>
    </div>
  );
}

function MetaBadge({ icon, label }) {
  return (
    <span className="meta-badge">
      {icon} {label}
    </span>
  );
}
