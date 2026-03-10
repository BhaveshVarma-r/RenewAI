import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import HumanQueue from './pages/HumanQueue';
import AuditTrace from './pages/AuditTrace';
import PolicyLookup from './pages/PolicyLookup';
import Demo from './pages/Demo';

const navItems = [
    { to: '/', label: 'Dashboard', icon: '📊' },
    { to: '/queue', label: 'Human Queue', icon: '👥' },
    { to: '/audit', label: 'Audit Trail', icon: '🔍' },
    { to: '/policies', label: 'Policies', icon: '📋' },
    { to: '/demo', label: 'Demo', icon: '🚀' },
];

export default function App() {
    return (
        <BrowserRouter>
            <div className="flex h-screen overflow-hidden">
                {/* Sidebar */}
                <nav className="w-64 bg-surface-900 border-r border-white/10 flex flex-col">
                    <div className="p-6 border-b border-white/10">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white font-bold text-lg">R</div>
                            <div>
                                <h1 className="text-lg font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">RenewAI</h1>
                                <p className="text-xs text-slate-500">Suraksha Life Insurance</p>
                            </div>
                        </div>
                    </div>
                    <div className="flex-1 py-4 space-y-1 px-3">
                        {navItems.map(item => (
                            <NavLink key={item.to} to={item.to} end
                                className={({ isActive }) => `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${isActive ? 'bg-primary-500/20 text-primary-400 shadow-lg shadow-primary-500/10' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'}`}>
                                <span className="text-lg">{item.icon}</span>
                                {item.label}
                            </NavLink>
                        ))}
                    </div>
                    <div className="p-4 border-t border-white/10">
                        <div className="glass-card p-3 text-xs text-slate-400">
                            <div className="flex items-center gap-2 mb-1"><div className="w-2 h-2 rounded-full bg-green-400 pulse-glow"></div> System Online</div>
                            <div>Gemini 2.0 Flash</div>
                        </div>
                    </div>
                </nav>

                {/* Main content */}
                <main className="flex-1 overflow-auto bg-gradient-to-br from-surface-900 via-surface-900 to-primary-900/20">
                    <div className="p-8">
                        <Routes>
                            <Route path="/" element={<Dashboard />} />
                            <Route path="/queue" element={<HumanQueue />} />
                            <Route path="/audit" element={<AuditTrace />} />
                            <Route path="/policies" element={<PolicyLookup />} />
                            <Route path="/demo" element={<Demo />} />
                        </Routes>
                    </div>
                </main>
            </div>
        </BrowserRouter>
    );
}
