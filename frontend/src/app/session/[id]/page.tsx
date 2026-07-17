"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  ApiError,
  completeSession,
  createRecord,
  getSession,
  goBackStep,
  requestFollowUp,
  submitStepResponse,
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { METHODOLOGY_STEPS, MIN_STEPS_TO_COMPLETE } from "@/lib/methodology-steps";
import { METHODOLOGY_LABELS } from "@/lib/types";
import type { SessionResponse } from "@/lib/types";

export default function SessionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { token } = useAuth();
  const router = useRouter();

  const [session, setSession] = useState<SessionResponse | null>(null);
  const [answer, setAnswer] = useState("");
  const [followUpQuestion, setFollowUpQuestion] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [lessonsLearned, setLessonsLearned] = useState("");
  const [recordTitle, setRecordTitle] = useState("");

  const loadSession = useCallback(async () => {
    if (!token) return;
    try {
      const data = await getSession(token, id);
      setSession(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Oturum yuklenemedi");
    }
  }, [token, id]);

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }
    loadSession();
  }, [token, loadSession, router]);

  if (!session) {
    return (
      <main>
        <p>{error ?? "Yukleniyor..."}</p>
      </main>
    );
  }

  const steps = METHODOLOGY_STEPS[session.methodology];
  const currentStepDef = steps[session.current_step];
  const minSteps = MIN_STEPS_TO_COMPLETE[session.methodology];
  const canComplete =
    session.status === "active" && Object.keys(session.answers).length >= minSteps;

  async function handleSubmitAnswer(event: React.FormEvent) {
    event.preventDefault();
    if (!token || !answer.trim()) return;
    setIsBusy(true);
    setError(null);
    try {
      const updated = await submitStepResponse(token, id, answer);
      setSession(updated);
      setAnswer("");
      setFollowUpQuestion(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Yanit gonderilemedi");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleFollowUp() {
    if (!token) return;
    setIsBusy(true);
    setError(null);
    try {
      const question = await requestFollowUp(token, id);
      setFollowUpQuestion(question);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Takip sorusu alinamadi");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleGoBack() {
    if (!token) return;
    setIsBusy(true);
    try {
      const updated = await goBackStep(token, id);
      setSession(updated);
    } finally {
      setIsBusy(false);
    }
  }

  async function handleComplete() {
    if (!token) return;
    setIsBusy(true);
    setError(null);
    try {
      const updated = await completeSession(token, id);
      setSession(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Oturum tamamlanamadi");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCreateRecord(event: React.FormEvent) {
    event.preventDefault();
    if (!token) return;
    setIsBusy(true);
    setError(null);
    try {
      const record = await createRecord(token, {
        session_id: id,
        title: recordTitle,
        lessons_learned: lessonsLearned,
      });
      router.push(`/knowledge?highlight=${record.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Kayit olusturulamadi");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <main>
      <section className="card stack">
        <div>
          <span className="badge">
            <span className={`badge-dot${session.status !== "active" ? "" : " offline"}`} />
            {METHODOLOGY_LABELS[session.methodology]} - {session.status}
          </span>
          <p>{session.problem_description}</p>
        </div>

        <div className="stack">
          {steps.map((step) =>
            session.answers[step.name] ? (
              <div key={step.name} className="card">
                <p className="step-indicator">{step.prompt}</p>
                <p>{session.answers[step.name]}</p>
              </div>
            ) : null,
          )}
        </div>

        {session.status === "active" && currentStepDef && (
          <form className="form-stack" onSubmit={handleSubmitAnswer}>
            <p className="step-indicator">
              Adim {session.current_step + 1}/{steps.length}
            </p>
            <label>
              {currentStepDef.prompt}
              <textarea
                required
                minLength={10}
                value={answer}
                onChange={(event) => setAnswer(event.target.value)}
              />
            </label>
            {followUpQuestion && <p className="hint-text">Takip sorusu: {followUpQuestion}</p>}
            {error && <p className="error-text">{error}</p>}
            <div className="row">
              <button className="button" type="submit" disabled={isBusy}>
                Gonder
              </button>
              <button
                className="button button-secondary"
                type="button"
                onClick={handleFollowUp}
                disabled={isBusy}
              >
                Takip Sorusu Iste
              </button>
              {session.current_step > 0 && (
                <button
                  className="button button-secondary"
                  type="button"
                  onClick={handleGoBack}
                  disabled={isBusy}
                >
                  Bir Adim Geri
                </button>
              )}
            </div>
          </form>
        )}

        {canComplete && (
          <button className="button" onClick={handleComplete} disabled={isBusy}>
            Oturumu Tamamla
          </button>
        )}

        {session.status === "completed" && (
          <form className="form-stack" onSubmit={handleCreateRecord}>
            <h2>Bilgi Bankasina Kaydet</h2>
            <label>
              Baslik
              <input
                required
                value={recordTitle}
                onChange={(event) => setRecordTitle(event.target.value)}
              />
            </label>
            <label>
              Ogrenilen Dersler (100-500 kelime)
              <textarea
                required
                value={lessonsLearned}
                onChange={(event) => setLessonsLearned(event.target.value)}
              />
              <span className="hint-text">
                {lessonsLearned.trim() ? lessonsLearned.trim().split(/\s+/).length : 0} kelime
              </span>
            </label>
            {error && <p className="error-text">{error}</p>}
            <button className="button" type="submit" disabled={isBusy}>
              Kaydi Olustur
            </button>
          </form>
        )}
      </section>
    </main>
  );
}
