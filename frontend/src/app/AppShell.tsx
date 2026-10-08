import type { ReactNode } from "react";
import { NavLink } from "react-router";

const NAVIGATION = [
  { to: "/senales", label: "Señales" },
  { to: "/explorar", label: "Explorar compras" },
  { to: "/casos", label: "Mis casos" },
  { to: "/admin", label: "Administración" },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <>
      <div className="demo-ribbon" role="note">
        <span>
          <b>MVP BETA · DATOS DE DEMOSTRACIÓN</b> · Todas las entidades, proveedores y montos son{" "}
          <b>ficticios</b>. Categoría del MVP: televisores.
        </span>
        <span>Seguimiento Compras Públicas · MVP Beta</span>
      </div>
      <header className="top">
        <div className="brand">
          <div className="logo" aria-hidden="true">
            ◎
          </div>
          Seguimiento Compras Públicas
        </div>
        <nav className="main" aria-label="Navegación principal">
          {NAVIGATION.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? "active" : undefined)}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main>{children}</main>
    </>
  );
}
