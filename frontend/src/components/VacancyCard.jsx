import React, { useState } from 'react';
import './VacancyCard.css';

/**
 *   vacancy: {
 *     title, company, salary, format, experience,
 *     skills, flags, flagColor, flagText, link,
 *     companyType, clusterName
 *   }
 */
export default function VacancyCard({ vacancy }) {
  const [expanded, setExpanded] = useState(false);

  const {
    title, company, salary, format, experience,
    skills = [], flags, flagColor, flagText,
    link, companyType, clusterName,
  } = vacancy;

  const companyBadge = {
    top:        { label: '⭐ Топ-10',       cls: 'badge-top' },
    accredited: { label: '✓ Аккредитована', cls: 'badge-acc' },
    regular:    { label: '',                cls: '' },
  }[companyType] || { label: '', cls: '' };

  return (
    <div className={`vacancy-card flag-${flagColor}`}>
      <div className="vc-header">
        <div className="vc-title-row">
          <a href={link} target="_blank" rel="noreferrer" className="vc-title">
            {title}
          </a>
          {flags > 0 && (
            <span className="flag-badge" title={flagText}>
              ⚠️ {flags}
            </span>
          )}
        </div>

        <div className="vc-meta">
          <span className="vc-company">
            {company}
            {companyBadge.label && (
              <span className={`company-badge ${companyBadge.cls}`}>
                {companyBadge.label}
              </span>
            )}
          </span>
          {clusterName && (
            <span className="vc-cluster">{clusterName}</span>
          )}
        </div>
      </div>

      <div className="vc-details">
        <span className="vc-chip">💰 {salary}</span>
        <span className="vc-chip">🕐 {experience}</span>
        <span className="vc-chip">📍 {format}</span>
      </div>

      {skills.length > 0 && (
        <div className="vc-skills">
          {(expanded ? skills : skills.slice(0, 6)).map((s, i) => (
            <span key={i} className="skill-tag">{s}</span>
          ))}
          {skills.length > 6 && (
            <button
              className="skills-toggle"
              onClick={() => setExpanded(e => !e)}
            >
              {expanded ? 'Скрыть' : `+${skills.length - 6} ещё`}
            </button>
          )}
        </div>
      )}

      {flagText && flags > 0 && (
        <details className="vc-flags">
          <summary>Подробнее о флагах</summary>
          <p>{flagText}</p>
        </details>
      )}
    </div>
  );
}
