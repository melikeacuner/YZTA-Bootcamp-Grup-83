import type { MethodologyType } from "./types";

export interface StepDefinition {
  name: string;
  prompt: string;
}

// NOT: backend'deki app/services/methodology/*_engine.py ile ayni adim/soru sirasini
// yansitir (UI'da adim metnini gostermek icin). Adimlar degisirse burasi da guncellenmeli.
export const METHODOLOGY_STEPS: Record<MethodologyType, StepDefinition[]> = {
  ishikawa: [
    { name: "man", prompt: "Insan (Man): Bu probleme insan/operator kaynakli hangi etkenler katkida bulunuyor?" },
    { name: "machine", prompt: "Makine (Machine): Ekipman/makine ile ilgili hangi etkenler soz konusu?" },
    { name: "method", prompt: "Yontem (Method): Surec/yontemle ilgili hangi etkenler soz konusu?" },
    { name: "material", prompt: "Malzeme (Material): Girdi/malzeme ile ilgili hangi etkenler soz konusu?" },
    { name: "measurement", prompt: "Olcum (Measurement): Olcum/kontrol ile ilgili hangi etkenler soz konusu?" },
    { name: "environment", prompt: "Ortam (Environment): Calisma ortamiyla ilgili hangi etkenler soz konusu?" },
  ],
  "8d": [
    { name: "d1_team", prompt: "D1 - Ekip: Problemi cozecek ekibi ve rollerini tanimlayin." },
    { name: "d2_problem_description", prompt: "D2 - Problem Tanimi: Problemi net ve olculebilir sekilde tanimlayin." },
    { name: "d3_containment_actions", prompt: "D3 - Gecici Onlemler: Etkiyi sinirlamak icin alinan acil onlemler nelerdir?" },
    { name: "d4_root_cause", prompt: "D4 - Kok Neden: Problemin kok nedeni nedir?" },
    { name: "d5_corrective_actions", prompt: "D5 - Duzeltici Faaliyetler: Kok nedeni ortadan kaldiracak faaliyetler nelerdir?" },
    { name: "d6_implementation", prompt: "D6 - Uygulama: Duzeltici faaliyetler nasil ve ne zaman uygulandi?" },
    { name: "d7_prevention", prompt: "D7 - Onleme: Benzer problemlerin tekrarini onlemek icin ne yapildi?" },
    { name: "d8_closure", prompt: "D8 - Kapanis: Ekip ve sonuc nasil onaylandi/kapatildi?" },
  ],
  "5why": Array.from({ length: 7 }, (_, i) => ({
    name: `why_${i + 1}`,
    prompt: `Neden ${i + 1}: Bir onceki nedenin sebebi nedir?`,
  })),
  pdca: [
    { name: "plan", prompt: "Plan: Problemi ve hedeflenen iyilestirmeyi planlayin." },
    { name: "do", prompt: "Do (Uygula): Plani kucuk olcekte/test olarak uygulayin." },
    { name: "check", prompt: "Check (Kontrol Et): Uygulama sonuclarini beklenenle karsilastirin." },
    { name: "act", prompt: "Act (Onlem Al): Sonuclara gore standartlastirin veya plani revize edin." },
  ],
};

export const MIN_STEPS_TO_COMPLETE: Record<MethodologyType, number> = {
  ishikawa: 6,
  "8d": 8,
  "5why": 3,
  pdca: 4,
};
