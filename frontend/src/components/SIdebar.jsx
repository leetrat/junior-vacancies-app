import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Sidebar.css';

// Подбор вакансий
const SURVEY_STEPS = [
    { path: '/',         icon: '📋', label: 'Опрос',       sessionKey: null },
    { path: '/clusters', icon: '🗂️', label: 'Кластеры',    sessionKey: 'surveyResult' },
    { path: '/result',   icon: '💼', label: 'Результаты',  sessionKey: 'clusterSelection' },
];

// Отдельные инструменты
const TOOLS = [
    { path: '/vacancy', icon: '🔍', label: 'Анализ вакансии' },
    { path: '/resume',  icon: '📄', label: 'Анализ резюме' },
];

export default function Sidebar() {
    const navigate  = useNavigate();
    const { pathname } = useLocation();

    // Путь активен если совпадает или является дочерним
    const isActive = (path) =>
        path === '/' ? pathname === '/' : pathname.startsWith(path);

    // Пункт доступен если нужный ключ в sessionStorage есть (или ключ не нужен)
    const isAvailable = (sessionKey) =>
        !sessionKey || !!sessionStorage.getItem(sessionKey);

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <span className="logo-icon">🎯</span>
                <span className="logo-text">Подбор вакансий</span>
            </div>

            {/* Подбор */}
            <nav className="sidebar-nav">
                <p className="nav-label">Подбор вакансий</p>
                {SURVEY_STEPS.map(item => {
                    const available = isAvailable(item.sessionKey);
                    const active    = isActive(item.path);
                    return (
                        <button
                            key={item.path}
                            className={`tab-btn ${active ? 'active' : ''} ${!available ? 'disabled' : ''}`}
                            onClick={() => available && navigate(item.path)}
                            title={!available ? 'Сначала пройдите предыдущий шаг' : ''}
                        >
                            <span className="tab-icon">{item.icon}</span>
                            {item.label}
                            {!available && <span className="lock-icon">🔒</span>}
                        </button>
                    );
                })}

                {/* Инструменты */}
                <p className="nav-label" style={{ marginTop: '16px' }}>Инструменты</p>
                {TOOLS.map(item => (
                    <button
                        key={item.path}
                        className={`tab-btn ${isActive(item.path) ? 'active' : ''}`}
                        onClick={() => navigate(item.path)}
                    >
                        <span className="tab-icon">{item.icon}</span>
                        {item.label}
                    </button>
                ))}
            </nav>
        </aside>
    );
}