"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError, loginUser, registerUser } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

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
      router.push("/session/new");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Beklenmeyen bir hata olustu");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main>
      <section className="card" style={{ maxWidth: 420, margin: "0 auto" }}>
        <h1>{mode === "login" ? "Giris Yap" : "Hesap Olustur"}</h1>
        <form className="form-stack" onSubmit={handleSubmit}>
          <label>
            E-posta
            <input
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label>
            Sifre
            <input
              type="password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            {mode === "register" && (
              <span className="hint-text">
                En az 8 karakter; buyuk/kucuk harf, rakam ve ozel karakter icermeli.
              </span>
            )}
          </label>
          {error && <p className="error-text">{error}</p>}
          <button className="button" type="submit" disabled={isSubmitting}>
            {mode === "login" ? "Giris Yap" : "Kayit Ol ve Giris Yap"}
          </button>
        </form>
        <p className="hint-text" style={{ marginTop: "1rem" }}>
          {mode === "login" ? "Hesabiniz yok mu? " : "Zaten hesabiniz var mi? "}
          <button
            className="link-button"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login" ? "Kayit olun" : "Giris yapin"}
          </button>
        </p>
      </section>
    </main>
  );
}
