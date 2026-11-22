export function LoadingState() {
  return (
    <main className="shell">
      <section className="state-panel" aria-live="polite">
        <div className="spinner" />
        <h1>Ładowanie lokalnego dashboardu</h1>
        <p>Odczyt aktualnego snapshotu przez lokalne API tylko do odczytu.</p>
      </section>
    </main>
  );
}
