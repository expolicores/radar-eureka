/** Keep the selected immutable run while opening/closing process evidence. */
export function researchProcessUrl(process: string, search: URLSearchParams) {
  const next = new URLSearchParams(search);
  next.set("process", process);
  next.delete("market");
  return `/explorar?${next}`;
}
