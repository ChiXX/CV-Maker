// Client-side LaTeX -> PDF compilation helper (WASM-based)
// This file provides a thin wrapper that will attempt to dynamically load
// a WASM LaTeX engine (e.g. tectonic-wasm) at runtime and compile a LaTeX
// string into a PDF Blob. If the WASM module is not available, the function
// will throw an error with guidance to enable the server fallback.

export async function compileLatexToPdf(latexSource: string): Promise<Blob> {
  // Lazy-load tectonic-wasm (or other WASM TeX engine)
  try {
    // Note: the exact package name / API may vary. This attempts a dynamic import.
    // Replace 'tectonic-wasm' with the actual package you choose and adapt usage.
    const tectonicModule = await import('tectonic-wasm').catch(() => null);

    if (!tectonicModule) {
      throw new Error(
        'Client LaTeX compiler not available. Install/enable tectonic-wasm or use server fallback.'
      );
    }

    // Common pattern: module.compile returns a Uint8Array PDF (API differs between packages)
    // Try a few common entry points; adapt as needed when integrating the chosen WASM.
    let pdfUint8: Uint8Array | null = null;

    // try compile() API
    if (typeof (tectonicModule as any).compile === 'function') {
      pdfUint8 = await (tectonicModule as any).compile(latexSource);
    } else if (typeof (tectonicModule as any).run === 'function') {
      // some builds expose run()/build()
      pdfUint8 = await (tectonicModule as any).run(latexSource);
    } else if ((tectonicModule as any).default && typeof (tectonicModule as any).default.compile === 'function') {
      pdfUint8 = await (tectonicModule as any).default.compile(latexSource);
    } else {
      throw new Error('Loaded WASM compiler does not expose a supported compile API.');
    }

    if (!pdfUint8) {
      throw new Error('Compiler did not return PDF data.');
    }

    // Ensure Uint8Array
    const uint8 = pdfUint8 instanceof Uint8Array ? pdfUint8 : new Uint8Array(pdfUint8);
    const blob = new Blob([uint8], { type: 'application/pdf' });
    return blob;
  } catch (err) {
    // Bubble a helpful error message for the UI
    const message = err instanceof Error ? err.message : String(err);
    throw new Error(`Client-side LaTeX compile failed: ${message}`);
  }
}


