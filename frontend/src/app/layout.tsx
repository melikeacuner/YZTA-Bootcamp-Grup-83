import type { Metadata } from "next";

import { Navbar } from "@/components/Navbar";
import { AuthProvider } from "@/lib/auth-context";

import "./globals.css";

export const metadata: Metadata = {
  title: "Proby AI",
  description:
    "Kurumsal problemleri sistematik metodolojiler ve yapay zeka destegiyle analiz eden bilgi yonetim platformu.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body>
        <AuthProvider>
          <Navbar />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
