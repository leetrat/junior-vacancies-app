import React, { useState } from 'react';
import './SkillFilter.css';

/**
 *   presetSkills:    string[]
 *   selectedSkills:  Set<string>
 *   onChange:        (newSet: Set<string>) => void
 */
export default function SkillFilter({ presetSkills = [], selectedSkills, onChange }) {
  const [customInput, setCustomInput] = useState('');

  function toggleSkill(skill) {
    const next = new Set(selectedSkills);
    if (next.has(skill)) next.delete(skill);
    else next.add(skill);
    onChange(next);
  }

  function addCustom() {
    const skill = customInput.trim();
    if (!skill) return;
    const next = new Set(selectedSkills);
    next.add(skill);
    onChange(next);
    setCustomInput('');
  }

  function removeSkill(skill) {
    const next = new Set(selectedSkills);
    next.delete(skill);
    onChange(next);
  }

  const customSkills = [...selectedSkills].filter(s => !presetSkills.includes(s));

  return (
    <div className="skill-filter">
      <h3 className="sf-title">🛠 Фильтрация по навыкам</h3>
      <p className="sf-hint">
        Выберите навыки — будут показаны только вакансии, в которых упомянут{' '}
        <strong>хотя бы один</strong>. Оставьте пустым, чтобы не фильтровать.
      </p>

      <div className="sf-chips">
        {presetSkills.map(skill => (
          <button
            key={skill}
            className={`skill-chip ${selectedSkills.has(skill) ? 'selected' : ''}`}
            onClick={() => toggleSkill(skill)}
          >
            {skill}
          </button>
        ))}

        {customSkills.map(skill => (
          <button key={skill} className="skill-chip selected custom">
            {skill}
            <span
              className="remove-btn"
              onClick={e => { e.stopPropagation(); removeSkill(skill); }}
            >×</span>
          </button>
        ))}
      </div>

      <div className="sf-add-row">
        <input
          type="text"
          value={customInput}
          placeholder="Добавить свой навык (напр. FastAPI, Airflow…)"
          onChange={e => setCustomInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addCustom(); } }}
        />
        <button className="btn-primary" onClick={addCustom}>+ Добавить</button>
      </div>
    </div>
  );
}
