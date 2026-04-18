import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { useRegister } from '../hooks/useAuth';
import { MessageSquare, Loader2, ArrowRight } from 'lucide-react';

export default function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const { mutate: register, isPending } = useRegister();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError('');
    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match');
      return;
    }
    register({ email, password });
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{ background: 'linear-gradient(135deg, #0B0F1A 0%, #111827 50%, #0B0F1A 100%)' }}
    >
      {/* Floating orbs */}
      <div className="absolute top-1/3 -right-20 w-72 h-72 rounded-full blur-3xl animate-float opacity-20"
        style={{ background: 'radial-gradient(circle, #6366F1, transparent)' }}
      />
      <div className="absolute bottom-1/3 -left-24 w-80 h-80 rounded-full blur-3xl animate-float opacity-15"
        style={{ background: 'radial-gradient(circle, #F472B6, transparent)', animationDelay: '2s' }}
      />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full blur-3xl opacity-5"
        style={{ background: 'radial-gradient(circle, #22D3EE, transparent)' }}
      />

      <div className="w-full max-w-md px-4 relative z-10 animate-fade-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-5"
            style={{
              background: 'linear-gradient(135deg, #6366F1, #F472B6)',
              boxShadow: '0 8px 30px rgba(99, 102, 241, 0.35)',
            }}
          >
            <MessageSquare size={26} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Create an account</h1>
          <p className="text-text-faint mt-1.5 text-sm">Get started with DocQ&A</p>
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
                placeholder="Min. 6 characters"
                className="input-glass"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-muted mb-1.5">Confirm Password</label>
              <input
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                placeholder="••••••••"
                className="input-glass"
              />
            </div>

            {error && (
              <p className="text-sm text-danger bg-danger/10 px-3 py-2 rounded-lg border border-danger/20">{error}</p>
            )}

            <button
              type="submit"
              disabled={isPending}
              className="btn-primary w-full !py-3 flex items-center justify-center gap-2"
            >
              {isPending ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <>
                  Create Account
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          <p className="text-center text-sm text-text-faint mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-light font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
