import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Proby AI",
  description:
    "Kurumsal problemleri sistematik metodolojiler ve yapay zeka destegiyle analiz eden bilgi yonetim platformu.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body>{children}</body>
    </html>
  );
}
