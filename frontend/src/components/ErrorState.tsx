interface ErrorStateProps {
  kind: 'api' | 'snapshot';
  detail?: string;
}

export function ErrorState({ kind, detail }: ErrorStateProps) {
  const title = kind === 'api' ? 'Lokalne API dashboardu jest niedostępne' : 'Brak poprawnego opublikowanego snapshotu dashboardu';
  const body =
    kind === 'api'
      ? 'Uruchom lokalne API tylko do odczytu i odśwież stronę.'
      : 'API działa, ale nie ma aktualnie poprawnego opublikowanego snapshotu.';

  return (
    <main className="shell">
      <section className="state-panel error">
        <h1>{title}</h1>
        <p>{body}</p>
        {detail ? <p className="muted">{detail}</p> : null}
      </section>
    </main>
  );
}
