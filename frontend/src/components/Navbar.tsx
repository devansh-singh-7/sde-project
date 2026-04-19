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
    <aside className="fixed top-0 left-0 h-screen w-64 flex flex-col z-50 bg-surface border-r border-border">
      {/* ── Logo ── */}
      <div className="px-6 py-7">
        <Link to="/" className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-sm bg-accent flex items-center justify-center">
            <MessageSquare size={16} className="text-white" />
          </div>
          <div>
            <span className="text-text font-semibold text-[15px] tracking-tight block leading-tight">DocQ&A</span>
            <span className="text-muted text-[11px] font-medium uppercase tracking-wide">AI Assistant</span>
          </div>
        </Link>
      </div>

      {/* ── Divider ── */}
      <div className="h-px bg-border w-full" />

      {/* ── Navigation ── */}
      <nav className="flex-1 px-4 py-5 flex flex-col gap-1">
        {links.map(({ to, label, icon: Icon }) => {
          const active = location.pathname === to || (to === '/documents' && location.pathname.startsWith('/documents'));
          return (
            <Link
              key={to}
              to={to}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-sm text-[13px] font-medium transition-colors group ${
                active
                  ? 'bg-accent/15 text-text'
                  : 'text-muted hover:text-text hover:bg-card'
              }`}
            >
              <Icon size={16} className={active ? 'text-accent' : 'text-muted group-hover:text-text transition-colors'} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* ── Upgrade hint ── */}
      <div className="mx-4 mb-4">
        <div className="rounded-md p-4 bg-card border border-border">
          <Sparkles size={16} className="text-accent mb-2" />
          <p className="text-[12px] text-muted leading-relaxed">
            AI-powered analysis for your documents, audio & video files.
          </p>
        </div>
      </div>

      {/* ── Divider ── */}
      <div className="h-px bg-border w-full" />

      {/* ── User ── */}
      <div className="px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-accent flex items-center justify-center text-[12px] font-semibold text-white shrink-0">
            {user?.email?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[13px] text-text font-medium truncate">{user?.email || 'User'}</p>
            <p className="text-[11px] text-muted">Free plan</p>
          </div>
          <button
            onClick={handleLogout}
            className="p-2 rounded-sm text-muted hover:text-coral hover:bg-coral/10 transition-colors"
            title="Logout"
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </aside>
  );
}
