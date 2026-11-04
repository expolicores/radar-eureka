import type { ReactNode } from "react";
import { NavLink, useLocation } from "react-router";

const NAVIGATION = [
  { to: "/eureka", label: "Eureka", icon: "M3 10 12 3l9 7v10H3Z M9 20v-7h6v7" },
  { to: "/eureka/alerts", label: "Alertas", icon: "M5 16h14l-2-4V8a5 5 0 0 0-10 0v4Z M10 20h4" },
  {
    to: "/eureka/revision",
    label: "Merecen Revisión",
    icon: "M9 5H5v16h14V5h-4 M9 3h6v4H9Z M8 12h8 M8 16h5",
  },
  {
    to: "/eureka/asistente",
    label: "Asistente Eureka",
    icon: "m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z",
  },
  { to: "/search", label: "Buscar SECOP", icon: "M16 16l5 5 M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0" },
  { to: "/eureka/operations", label: "Operación", icon: "M3 17h3l4-10 4 14 4-10h3" },
  {
    to: "/eureka/licitaciones",
    label: "Licitaciones.info (CDP)",
    icon: "M3 5h18v14H3Z M3 9h18 M7 13h4 M7 16h9",
  },
  { to: "/senales", label: "Señales", icon: "M3 20h18 M6 16v-4 M12 16V4 M18 16V8" },
  { to: "/explorar", label: "Explorar compras", icon: "M3 7h18v14H3Z M8 7V3h8v4 M3 12h18" },
  { to: "/casos", label: "Mis casos", icon: "M3 5h7l2 3h9v13H3Z" },
  { to: "/admin", label: "Administración", icon: "M4 7h16 M4 17h16 M8 4v6 M16 14v6" },
];

function Icon({ path }: { path: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={path} />
    </svg>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = useLocation().pathname;
  const isEureka = pathname.startsWith("/eureka") || pathname.startsWith("/search");
  const isResearch = pathname === "/explorar" || pathname === "/senales";
  const current = [...NAVIGATION]
    .reverse()
    .find((item) => pathname === item.to || pathname.startsWith(`${item.to}/`));
  return (
    <div className="radar-shell">
      <aside className="radar-sidebar">
        <NavLink to="/eureka" className="radar-brand" aria-label="Radar · Inicio">
          <span className="radar-mark" aria-hidden="true">
            <Icon path="M12 3a9 9 0 1 0 9 9 M12 7a5 5 0 1 0 5 5 M12 12l8-8 M12 12h.01" />
          </span>
          <span>
            Radar<small>INTELIGENCIA COMERCIAL</small>
          </span>
        </NavLink>
        <p className="radar-nav-label">ESPACIO DE TRABAJO</p>
        <nav className="radar-navigation" aria-label="Navegación principal">
          {NAVIGATION.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/eureka"}
              className={({ isActive }) => (isActive ? "active" : undefined)}
            >
              <Icon path={item.icon} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="radar-sidebar-footer">
          <span className="radar-footer-symbol">R</span>
          <div>
            Radar Eureka<small>De la información a la decisión</small>
          </div>
        </div>
      </aside>
      <div className="radar-workspace">
        <header className="radar-header">
          <div className="radar-breadcrumb">
            Radar <span>/</span> <strong>{current?.label ?? "Compras públicas"}</strong>
          </div>
          <div className="radar-header-meta">
            <span>Colombia</span>
            <span className="radar-avatar" aria-hidden="true">
              RE
            </span>
          </div>
        </header>
        <div className="radar-context" role="note">
          {isResearch ? (
            <span>
              <b>INVESTIGACIÓN · SECOP REAL</b> · Muestra exploratoria con evidencia y limitaciones
              explícitas.
            </span>
          ) : isEureka ? (
            <span>
              <b>INTELIGENCIA EN CONTRATACIÓN · PROCESOS SECOP</b> · Confirma vigencia y requisitos
              antes de participar.
            </span>
          ) : (
            <span>
              <b>DATOS DE DEMOSTRACIÓN</b> · Entidades, proveedores y montos ficticios.
            </span>
          )}
        </div>
        <main className="radar-main">{children}</main>
      </div>
    </div>
  );
}
