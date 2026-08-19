
export default function Home() {
  return (
    <main className="min-h-[calc(100vh-4rem)]">

      <section className="mx-auto max-w-7xl px-6 py-24">
        <div className="max-w-3xl">
          <div className="mb-6 font-mono text-xs font-medium uppercase tracking-[0.18em] text-orange-600">
            Sprawozdania laboratoryjne
          </div>

          <h1 className="text-5xl font-semibold leading-[1.08] tracking-tight text-neutral-950 sm:text-6xl">
            Od pomiarów do gotowego sprawozdania.
          </h1>

          <p className="mt-6 max-w-2xl text-lg leading-8 text-neutral-600">
            Dodaj instrukcję laboratoryjną oraz wyniki pomiarów.
            Sprawko przygotuje obliczenia, wykresy, analizę i dokument
            gotowy do dalszej edycji.
          </p>

          <div className="mt-10 flex items-center gap-4">
            <button className="rounded-lg bg-orange-500 px-5 py-3 text-sm font-medium text-white hover:bg-orange-600">
              Utwórz sprawozdanie
            </button>

            <button className="rounded-lg border border-neutral-300 bg-white px-5 py-3 text-sm font-medium text-neutral-700 hover:bg-neutral-50">
              Zobacz jak działa
            </button>
          </div>
        </div>

        <div className="mt-24 grid gap-4 border-t border-neutral-200 pt-8 sm:grid-cols-3">
          <div>
            <div className="font-mono text-xs text-neutral-400">
              01 / DANE
            </div>
            <h2 className="mt-3 font-medium text-neutral-900">
              Dodaj pomiary
            </h2>
            <p className="mt-2 text-sm leading-6 text-neutral-500">
              Wgraj arkusz Excel zawierający dane z laboratorium.
            </p>
          </div>

          <div>
            <div className="font-mono text-xs text-neutral-400">
              02 / ANALIZA
            </div>
            <h2 className="mt-3 font-medium text-neutral-900">
              Przetwarzanie
            </h2>
            <p className="mt-2 text-sm leading-6 text-neutral-500">
              Obliczenia i wykresy wykonywane są na podstawie instrukcji.
            </p>
          </div>

          <div>
            <div className="font-mono text-xs text-neutral-400">
              03 / RAPORT
            </div>
            <h2 className="mt-3 font-medium text-neutral-900">
              Gotowe sprawozdanie
            </h2>
            <p className="mt-2 text-sm leading-6 text-neutral-500">
              Przejrzyj wynik i pobierz dokument DOCX.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}