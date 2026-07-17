"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth-context";

export function Navbar() {
  const { token, logout, isLoading } = useAuth();
  const router = useRouter();

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <nav className="navbar">
      <Link href="/" className="navbar-brand">
        Proby AI
      </Link>
      <div className="navbar-links">
        {!isLoading && token && (
          <>
            <Link href="/session/new">Yeni Problem</Link>
            <Link href="/knowledge">Bilgi Bankasi</Link>
            <button className="link-button" onClick={handleLogout}>
              Cikis Yap
            </button>
          </>
        )}
        {!isLoading && !token && <Link href="/login">Giris Yap</Link>}
      </div>
    </nav>
  );
}
