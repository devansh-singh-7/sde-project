import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { useLogin } from '../hooks/useAuth';
import { MessageSquare, Loader2, ArrowRight } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { mutate: login, isPending } = useLogin();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    login({ username: email, password });
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{ background: 'linear-gradient(135deg, #0B0F1A 0%, #111827 50%, #0B0F1A 100%)' }}
    >
      {/* Floating orbs */}
      <div className="absolute top-1/4 -left-20 w-72 h-72 rounded-full blur-3xl animate-float opacity-20"
        style={{ background: 'radial-gradient(circle, #6366F1, transparent)' }}
      />
      <div className="absolute bottom-1/4 -right-20 w-80 h-80 rounded-full blur-3xl animate-float opacity-15"
        style={{ background: 'radial-gradient(circle, #22D3EE, transparent)', animationDelay: '3s' }}
      />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full blur-3xl opacity-5"
        style={{ background: 'radial-gradient(circle, #F472B6, transparent)' }}
      />

      <div className="w-full max-w-md px-4 relative z-10 animate-fade-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-5"
            style={{
              background: 'linear-gradient(135deg, #6366F1, #22D3EE)',
              boxShadow: '0 8px 30px rgba(99, 102, 241, 0.35)',
            }}
          >
            <MessageSquare size={26} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Welcome back</h1>
          <p className="text-text-faint mt-1.5 text-sm">Sign in to your DocQ&A account</p>
        </div>

        {/* Card */}
        <div className="glass-card p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-text-muted mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
                className="input-glass"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-muted mb-1.5">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
                className="input-glass"
              />
            </div>
            <button
              type="submit"
              disabled={isPending}
              className="btn-primary w-full !py-3 flex items-center justify-center gap-2"
            >
              {isPending ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <>
                  Sign In
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          <p className="text-center text-sm text-text-faint mt-6">
            Don't have an account?{' '}
            <Link to="/register" className="text-primary-light font-medium hover:underline">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
