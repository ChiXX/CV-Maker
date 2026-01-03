// Client-side LaTeX -> PDF compilation helper (WASM-based)
// This file provides a thin wrapper that will attempt to dynamically load
// a WASM LaTeX engine (e.g. tectonic-wasm) at runtime and compile a LaTeX
// string into a PDF Blob. If the WASM module is not available, the function
// will throw an error with guidance to enable the server fallback.

export async function compileLatexToPdf(latexSource: string): Promise<Blob> {
  // Client-side LaTeX compilation is not currently implemented
  // This function throws an error to direct users to server-side compilation
  throw new Error(
    'Client-side LaTeX compilation not available. Please use the server fallback or download options.'
  );
}


