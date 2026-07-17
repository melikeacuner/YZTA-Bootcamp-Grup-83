"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError, createSession } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { METHODOLOGY_LABELS, type MethodologyType } from "@/lib/types";

const METHODOLOGIES = Object.keys(METHODOLOGY_LABELS) as MethodologyType[];

export default function NewSessionPage() {
  const [methodology, setMethodology] = useState<MethodologyType>("5why");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { token } = useAuth();
  const router = useRouter();

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!token) {
      router.push("/login");
      return;
    }
    setError(null);
    setIsSubmitting(true);

    try {
      const session = await createSession(token, methodology, description);
      router.push(`/session/${session.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Beklenmeyen bir hata olustu");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main>
      <section className="card stack">
        <div>
          <h1>Yeni Problem Kaydi</h1>
          <p className="hint-text">
            Problemi tanimlayin ve bir cozum metodolojisi secin. Metodoloji size adim adim
            rehberlik edecek.
          </p>
        </div>

        <form className="form-stack" onSubmit={handleSubmit}>
          <div>
            <p style={{ marginBottom: "0.5rem" }}>Metodoloji</p>
            <div className="methodology-grid">
              {METHODOLOGIES.map((option) => (
                <button
                  type="button"
                  key={option}
                  className={`methodology-option${methodology === option ? " selected" : ""}`}
                  onClick={() => setMethodology(option)}
                >
                  {METHODOLOGY_LABELS[option]}
                </button>
              ))}
            </div>
          </div>

          <label>
            Problem Aciklamasi (20-2000 karakter)
            <textarea
              required
              minLength={20}
              maxLength={2000}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Problemi mumkun oldugunca detayli aciklayin..."
            />
            <span className="hint-text">{description.length}/2000 karakter</span>
          </label>

          {error && <p className="error-text">{error}</p>}

          <button className="button" type="submit" disabled={isSubmitting}>
            Oturumu Baslat
          </button>
        </form>
      </section>
    </main>
  );
}
