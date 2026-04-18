import { Link, useLocation } from 'react-router-dom';
import { LogOut, FileText, LayoutDashboard, MessageSquare, Sparkles } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { useLogout } from '../hooks/useAuth';

export default function Navbar() {
  const user = useAuthStore((s) => s.user);
  const handleLogout = useLogout();
  const location = useLocation();

  const links = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/documents', label: 'Documents', icon: FileText },
  ];

  return (
    <aside className="fixed top-0 left-0 h-screen w-64 flex flex-col z-50"
      style={{
        background: 'linear-gradient(180deg, rgba(8, 12, 25, 0.92) 0%, rgba(15, 23, 42, 0.88) 100%)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderRight: '1px solid rgba(148, 163, 184, 0.08)',
      }}
    >
      {/* ── Logo ── */}
      <div className="px-6 py-7">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center relative overflow-hidden"
            style={{ background: 'linear-gradient(135deg, #6366F1, #22D3EE)' }}
          >
            <MessageSquare size={20} className="text-white relative z-10" />
            <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          </div>
          <div>
            <span className="text-white font-bold text-lg tracking-tight block leading-tight">DocQ&A</span>
            <span className="text-text-faint text-[10px] font-medium uppercase tracking-widest">AI Assistant</span>
          </div>
        </Link>
      </div>

      {/* ── Divider ── */}
      <div className="mx-5 h-px" style={{ background: 'linear-gradient(90deg, transparent, rgba(99,102,241,0.2), transparent)' }} />

      {/* ── Navigation ── */}
      <nav className="flex-1 px-4 py-5 flex flex-col gap-1">
        {links.map(({ to, label, icon: Icon }) => {
          const active = location.pathname === to || (to === '/documents' && location.pathname.startsWith('/documents'));
          return (
            <Link
              key={to}
              to={to}
              className={`
                flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 relative group
                ${active
                  ? 'text-white'
                  : 'text-text-muted hover:text-white'
                }
              `}
              style={active ? {
                background: 'rgba(99, 102, 241, 0.15)',
                boxShadow: '0 0 20px rgba(99, 102, 241, 0.1)',
              } : {}}
            >
              {active && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-r-full bg-primary" />
              )}
              <Icon size={18} className={active ? 'text-primary-light' : 'text-text-faint group-hover:text-text-muted transition-colors'} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* ── Upgrade hint ── */}
      <div className="mx-4 mb-4">
        <div className="rounded-xl p-4 relative overflow-hidden"
          style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.12), rgba(34,211,238,0.08))' }}
        >
          <div className="absolute top-0 right-0 w-20 h-20 rounded-full blur-2xl opacity-30"
            style={{ background: 'radial-gradient(circle, #6366F1, transparent)' }}
          />
          <Sparkles size={18} className="text-primary-light mb-2" />
          <p className="text-xs text-text-muted leading-relaxed">
            AI-powered analysis for your documents, audio & video files.
          </p>
        </div>
      </div>

      {/* ── Divider ── */}
      <div className="mx-5 h-px" style={{ background: 'linear-gradient(90deg, transparent, rgba(148,163,184,0.1), transparent)' }} />

      {/* ── User ── */}
      <div className="px-4 py-4">
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0"
            style={{ background: 'linear-gradient(135deg, #6366F1, #22D3EE)' }}
          >
            {user?.email?.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-white font-medium truncate">{user?.email}</p>
            <p className="text-[10px] text-text-faint">Free plan</p>
          </div>
          <button
            onClick={handleLogout}
            className="p-2 rounded-lg text-text-faint hover:text-danger hover:bg-danger/10 transition-all duration-200"
            title="Logout"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}
