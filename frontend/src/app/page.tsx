"use client";

import { useAuth } from "@/lib/auth-context";
import Dashboard from "@/components/dashboard";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Loader2 } from "lucide-react";

export default function HomePage() {
  const { token, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !token) {
      router.push("/login");
    }
  }, [token, isLoading, router]);

  if (isLoading) {
    return (
      <div className="w-screen h-screen flex flex-col items-center justify-center bg-[#030a10] text-[#80deea]">
        <Loader2 className="w-10 h-10 animate-spin text-[#00e5ff]" />
        <p className="text-xs font-mono mt-3">Proby AI Yükleniyor...</p>
      </div>
    );
  }

  if (!token) {
    return null; // Will redirect via useEffect
  }

  return <Dashboard />;
}
