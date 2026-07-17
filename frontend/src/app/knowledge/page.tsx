"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError, searchKnowledge } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { KnowledgeSearchResult } from "@/lib/types";

export default function KnowledgePage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<KnowledgeSearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const { token } = useAuth();
  const router = useRouter();

  async function handleSearch(event: React.FormEvent) {
    event.preventDefault();
    if (!token) {
      router.push("/login");
      return;
    }
    setError(null);
    setIsSearching(true);
    try {
      const data = await searchKnowledge(token, query);
      setResults(data);
      setHasSearched(true);
    } catch (err) {
      if (err instanceof ApiError && err.status === 503) {
        setError("Semantik arama gecici olarak kullanilamiyor, lutfen daha sonra tekrar deneyin.");
      } else {
        setError(err instanceof ApiError ? err.message : "Arama basarisiz oldu");
      }
    } finally {
      setIsSearching(false);
    }
  }

  return (
    <main>
      <section className="card stack">
        <div>
          <h1>Bilgi Bankasi</h1>
          <p className="hint-text">
            Daha once cozulmus benzer problemleri anlamsal arama ile bulun.
          </p>
        </div>

        <form className="row" onSubmit={handleSearch}>
          <input
            style={{ flex: 1, minWidth: 240 }}
            required
            minLength={10}
            maxLength={500}
            placeholder="Orn: bant hattinda tekrarlayan duraksama..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <button className="button" type="submit" disabled={isSearching}>
            Ara
          </button>
        </form>

        {error && <p className="error-text">{error}</p>}

        {hasSearched && results.length === 0 && !error && (
          <p className="hint-text">Sonuc bulunamadi.</p>
        )}

        <ul className="record-list">
          {results.map((result) => (
            <li key={result.id}>
              <p className="step-indicator">Benzerlik skoru: {result.score.toFixed(2)}</p>
              <p style={{ fontWeight: 600 }}>{result.title ?? "Basliksiz kayit"}</p>
              <p className="hint-text">
                {result.methodology} {result.industry ? `· ${result.industry}` : ""}{" "}
                {result.department ? `· ${result.department}` : ""}
              </p>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
