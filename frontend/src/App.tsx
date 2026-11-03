import { Navigate, Route, Routes } from "react-router";

import { AppShell } from "./app/AppShell";
import { CasesPage } from "./features/cases/CasesPage";
import { ExplorePage } from "./features/explore/ExplorePage";
import { PendingSection } from "./features/pending/PendingSection";
import { PurchaseDetailPage } from "./features/purchase/PurchaseDetailPage";
import { SignalDetailPage } from "./features/signal-detail/SignalDetailPage";
import { SignalsPage } from "./features/signals/SignalsPage";
import { EurekaPage } from "./features/eureka/EurekaPage";
import { HumanReviewPage } from "./features/eureka/HumanReviewPage";
import { EurekaDetailPage } from "./features/eureka/EurekaDetailPage";
import { EurekaAlertsPage } from "./features/eureka/EurekaAlertsPage";
import { SearchPage } from "./features/search/SearchPage";
import { EurekaNotificationsPage } from "./features/eureka/EurekaNotificationsPage";
import { OperationsPage } from "./features/operations/OperationsPage";
import { LicitacionesPage } from "./features/licitaciones/LicitacionesPage";
import { AssistantPage } from "./features/assistant/AssistantPage";

export function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/senales" replace />} />
        <Route path="/explorar" element={<ExplorePage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/eureka" element={<EurekaPage />} />
        <Route path="/eureka/asistente" element={<AssistantPage />} />
        <Route path="/eureka/revision" element={<HumanReviewPage />} />
        <Route path="/eureka/revision/:identity" element={<HumanReviewPage />} />
        <Route path="/eureka/alerts" element={<EurekaAlertsPage />} />
        <Route path="/eureka/alerts/:alertId" element={<EurekaAlertsPage />} />
        <Route path="/eureka/notifications" element={<EurekaNotificationsPage />} />
        <Route path="/eureka/operations" element={<OperationsPage />} />
        <Route path="/eureka/licitaciones" element={<LicitacionesPage />} />
        <Route path="/eureka/:opportunityId" element={<EurekaDetailPage />} />
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
