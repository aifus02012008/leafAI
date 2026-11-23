import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Leaf, Eye, EyeOff, Lock, Mail, UserPlus, Loader2, CheckCircle2 } from 'lucide-react';
import { apiRegister } from '../api/auth';
import { useAuth } from '../contexts/AuthContext';
import { showToast } from '../components/Toast';

export function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirmation, setPasswordConfirmation] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email || !password || !passwordConfirmation) {
      showToast('error', 'Vui lòng điền đầy đủ tất cả các trường thông tin.');
      return;
    }
    if (password.length < 8) {
      showToast('error', 'Mật khẩu phải có độ dài tối thiểu 8 ký tự.');
      return;
    }
    if (password !== passwordConfirmation) {
      showToast('error', 'Mật khẩu xác nhận không trùng khớp.');
      return;
    }

    setLoading(true);
    try {
      const res = await apiRegister(email, password, passwordConfirmation);
      login(res.access_token, res.user);
      showToast('success', 'Đã tạo tài khoản.');
      navigate('/dashboard');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Đăng ký thất bại. Vui lòng kiểm tra lại thông tin.';
      showToast('error', msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-transparent flex items-center justify-center p-4 sm:p-6 lg:p-8 font-sans">
      <div className="w-full max-w-4xl bg-white/92 backdrop-blur-xl rounded-3xl border border-[#DCE5DC] shadow-2xl overflow-hidden grid grid-cols-1 lg:grid-cols-12 animate-in fade-in zoom-in-95 duration-200">
        {/* Left Side: Brand & Value Prop */}
        <div className="lg:col-span-5 bg-forest text-white p-8 sm:p-10 flex flex-col justify-between relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-400/10 rounded-full blur-2xl pointer-events-none -mr-16 -mt-16" />
          <div className="absolute bottom-0 left-0 w-52 h-52 bg-emerald-900/30 rounded-full blur-xl pointer-events-none -ml-12 -mb-12" />

          <div className="relative z-10">
            <div className="inline-flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white/15 backdrop-blur-md border border-white/25 flex items-center justify-center text-white shadow-sm">
                <Leaf className="w-5 h-5 text-emerald-200" />
              </div>
              <div>
                <span className="font-extrabold text-lg tracking-tight font-display">
                  LEAF_AI
                </span>
              </div>
            </div>

            <h2 className="mt-12 text-3xl font-extrabold tracking-tight font-display leading-tight">
              Chụp lá,<br /><span className="text-[#5EE6A0]">biết bệnh.</span>
            </h2>
          </div>
        </div>

        {/* Right Side: Form */}
        <div className="lg:col-span-7 p-8 sm:p-12 flex flex-col justify-center">
          <div className="max-w-md mx-auto w-full">
            <div className="mb-8">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-[#10201A] tracking-tight font-display">
                Tạo tài khoản
              </h1>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <Mail size={14} className="text-[#1F7A4D]" />
                  Email
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="kysu@nongnghiep.vn"
                  className="input-clean"
                  autoComplete="email"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <Lock size={14} className="text-[#1F7A4D]" />
                  Mật khẩu (≥ 8 ký tự)
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="input-clean pr-11"
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiển thị mật khẩu'}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 transition-colors cursor-pointer"
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <CheckCircle2 size={14} className="text-[#1F7A4D]" />
                  Nhập lại mật khẩu
                </label>
                <input
                  type="password"
                  required
                  value={passwordConfirmation}
                  onChange={(e) => setPasswordConfirmation(e.target.value)}
                  placeholder="••••••••"
                  className="input-clean"
                  autoComplete="new-password"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full btn-primary mt-4 py-3 text-sm font-semibold justify-center"
              >
                {loading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Đang tạo…</span>
                  </>
                ) : (
                  <>
                    <UserPlus size={16} />
                    <span>Tạo tài khoản</span>
                  </>
                )}
              </button>
            </form>

            <div className="mt-8 pt-6 border-t border-[#DCE5DC] text-center">
              <p className="text-xs sm:text-sm text-slate-600">
                
                <Link
                  to="/login"
                  className="font-bold text-[#1F7A4D] hover:text-[#17603C] underline underline-offset-4"
                >
                  Đăng nhập
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
