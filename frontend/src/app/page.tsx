"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { fetchHealth } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function HomePage() {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const { token } = useAuth();

  useEffect(() => {
    fetchHealth()
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false));
  }, []);

  return (
    <main>
      <section className="card stack">
        <div>
          <h1>Proby AI</h1>
          <p>
            Kurumsal problemleri Ishikawa, 8D, 5 Why ve PDCA metodolojileriyle analiz eden,
            çözümleri kurumsal bilgi bankasına dönüştüren platform.
          </p>
          <p className="badge">
            <span className={`badge-dot${backendOnline ? "" : " offline"}`} />
            {backendOnline === null
              ? "Backend durumu kontrol ediliyor..."
              : backendOnline
                ? "Backend calisiyor"
                : "Backend'e ulasilamiyor"}
          </p>
        </div>

        <div className="row">
          {token ? (
            <>
              <Link className="button" href="/session/new">
                Yeni Problem Baslat
              </Link>
              <Link className="button button-secondary" href="/knowledge">
                Bilgi Bankasinda Ara
              </Link>
            </>
          ) : (
            <Link className="button" href="/login">
              Giris Yap / Kayit Ol
            </Link>
          )}
        </div>
      </section>
    </main>
  );
}
