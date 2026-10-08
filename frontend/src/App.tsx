import { Navigate, Route, Routes } from "react-router";

import { AppShell } from "./app/AppShell";
import { CasesPage } from "./features/cases/CasesPage";
import { ExplorePage } from "./features/explore/ExplorePage";
import { PendingSection } from "./features/pending/PendingSection";
import { PurchaseDetailPage } from "./features/purchase/PurchaseDetailPage";
import { SignalDetailPage } from "./features/signal-detail/SignalDetailPage";
import { SignalsPage } from "./features/signals/SignalsPage";

export function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/senales" replace />} />
        <Route path="/explorar" element={<ExplorePage />} />
        <Route path="/senales" element={<SignalsPage />} />
        <Route path="/senales/:code" element={<SignalDetailPage />} />
        <Route path="/casos" element={<CasesPage />} />
        <Route path="/casos/:caseId" element={<CasesPage />} />
        <Route path="/admin" element={<PendingSection title="Administración y operación" />} />
        <Route path="/compras/:purchaseId" element={<PurchaseDetailPage />} />
        <Route path="*" element={<PendingSection title="Página no encontrada" />} />
      </Routes>
    </AppShell>
  );
}
