export function PendingSection({ title }: { title: string }) {
  return (
    <section>
      <h1>{title}</h1>
      <div className="notice info" role="status">
        <span aria-hidden="true">ⓘ</span>
        <div>Disponible en un próximo incremento del MVP Beta.</div>
      </div>
    </section>
  );
}
