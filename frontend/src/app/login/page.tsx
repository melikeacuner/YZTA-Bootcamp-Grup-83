"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ApiError, loginUser, registerUser } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { AlertCircle, LogIn, UserPlus, Sparkles } from "lucide-react";

export default function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login } = useAuth();
  const router = useRouter();

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (mode === "register") {
        await registerUser(email, password);
      }
      const token = await loginUser(email, password);
      login(token.access_token);
      router.push("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Beklenmeyen bir hata oluştu");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleTestLogin() {
    setError(null);
    setIsSubmitting(true);
    const randomSuffix = Math.floor(1000 + Math.random() * 9000);
    const testEmail = `test_${randomSuffix}@pkm.com`;
    const testPassword = "Password123!";

    try {
      let tokenData;
      try {
        tokenData = await loginUser(testEmail, testPassword);
      } catch (loginErr) {
        try {
          await registerUser(testEmail, testPassword);
          tokenData = await loginUser(testEmail, testPassword);
        } catch (regErr) {
          throw new Error("Test kullanıcısı oluşturulamadı veya giriş yapılamadı.");
        }
      }
      
      if (tokenData && tokenData.access_token) {
        login(tokenData.access_token);
        router.push("/");
      }
    } catch (err: any) {
      setError(err.message || "Hızlı test girişi başarısız.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="w-screen h-screen flex items-center justify-center bg-[#030a10] px-4 overflow-hidden relative">
      {/* Glow decorative graphics */}
      <div className="absolute top-0 right-0 w-[400px] h-[400px] rounded-full bg-[radial-gradient(circle_at_center,rgba(0,229,255,0.02),transparent_70%)] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] rounded-full bg-[radial-gradient(circle_at_center,rgba(124,77,255,0.02),transparent_70%)] pointer-events-none" />

      <section className="w-full max-w-md bg-[#061320] border border-[#10293f] rounded-2xl p-8 shadow-2xl relative overflow-hidden animate-fade-in">
        <div className="absolute top-0 left-0 right-0 h-[2.5px] bg-gradient-to-r from-[#00e5ff] to-[#7c4dff]" />

        <div className="text-center mb-8 space-y-1">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#00e5ff] to-[#7c4dff] flex items-center justify-center font-bold text-[#030a10] text-2xl mx-auto shadow-md shadow-cyan-500/10">
            P
          </div>
          <h1 className="text-xl font-bold text-[#e0f7fa] tracking-wide pt-3">
            {mode === "login" ? "Proby AI'a Giriş Yap" : "Yeni Hesap Oluştur"}
          </h1>
          <p className="text-xs text-[#80deea]">Kurumsal problem çözme ve bilgi yönetim platformu</p>
        </div>

        <form className="space-y-5 text-xs" onSubmit={handleSubmit}>
          <div className="flex flex-col gap-1.5">
            <label className="font-semibold text-[#80deea]">E-posta Adresi</label>
            <input
              type="email"
              required
              placeholder="isim@sirket.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="p-3 bg-[#030a10] border border-[#10293f] rounded-lg text-sm text-[#e0f7fa]"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="font-semibold text-[#80deea]">Şifre</label>
            <input
              type="password"
              required
              placeholder="••••••••"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="p-3 bg-[#030a10] border border-[#10293f] rounded-lg text-sm text-[#e0f7fa]"
            />
            {mode === "register" && (
              <span className="text-[10px] text-[#4f7b92] mt-1">
                En az 8 karakter; büyük/küçük harf, rakam ve özel karakter içermelidir.
              </span>
            )}
          </div>

          {error && (
            <div className="p-3 bg-red-950/20 border border-red-500/30 rounded-lg flex items-center gap-2 text-red-400 text-[11px] leading-relaxed">
              <AlertCircle size={14} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button className="btn btn-primary w-full py-3 text-xs flex items-center justify-center gap-2" type="submit" disabled={isSubmitting}>
            {mode === "login" ? (
              <>
                <LogIn size={14} />
                <span>Giriş Yap</span>
              </>
            ) : (
              <>
                <UserPlus size={14} />
                <span>Kayıt Ol ve Giriş Yap</span>
              </>
            )}
          </button>

          <div className="relative flex py-2 items-center">
            <div className="flex-grow border-t border-[#10293f]/50"></div>
            <span className="flex-shrink mx-4 text-[#4f7b92] text-[10px]">Veya</span>
            <div className="flex-grow border-t border-[#10293f]/50"></div>
          </div>

          <button
            type="button"
            onClick={handleTestLogin}
            disabled={isSubmitting}
            className="w-full py-3 bg-[#0f2438] border border-cyan-500/30 text-cyan-400 rounded-lg text-xs font-semibold hover:bg-cyan-500/10 transition flex items-center justify-center gap-2"
          >
            <Sparkles size={14} className="text-cyan-400" />
            <span>Hızlı Test Girişi (Auto Login)</span>
          </button>
        </form>

        <p className="text-[11px] text-[#4f7b92] text-center mt-6">
          {mode === "login" ? "Hesabınız yok mu? " : "Zaten hesabınız var mı? "}
          <button
            className="text-[#00e5ff] hover:underline bg-transparent border-none p-0 cursor-pointer"
            onClick={() => {
              setError(null);
              setMode(mode === "login" ? "register" : "login");
            }}
          >
            {mode === "login" ? "Kayıt olun" : "Giriş yapın"}
          </button>
        </p>
      </section>
    </main>
  );
}
