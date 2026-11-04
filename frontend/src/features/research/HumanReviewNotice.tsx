export type ResearchHumanReview = {
  human_review_recommended: boolean;
  human_review_reasons: string[];
  review_status?: string;
};

const REASONS: Record<string, string> = {
  missing_itemized_contract_price: "Falta el precio final desglosado del producto.",
  missing_accepted_offer: "No se pudo demostrar cuál oferta económica fue aceptada para este ítem.",
  ambiguous_product_identity: "La identidad del producto no se pudo resolver con confianza.",
  conflicting_product_reference:
    "Existe conflicto entre referencias de producto, como las de 55″ y 70″.",
  global_contract_value_without_item_breakdown:
    "El contrato publica un valor global, sin precio final atribuible al televisor.",
  missing_quantity: "Falta una cantidad verificable del producto.",
  incomplete_document_cycle: "El ciclo documental disponible está incompleto.",
  unresolved_document_relationship:
    "No se pudo vincular con seguridad la evidencia entre documentos.",
  extraction_failure: "Un documento no pudo extraerse correctamente.",
  oversized_document: "El documento supera los límites de procesamiento configurados.",
  ambiguous_winning_offer:
    "Conocer al ganador no demuestra qué cotización o precios fueron aceptados.",
  contract_documents_found_but_not_resolved:
    "Se encontraron documentos por contrato, pero no se resolvió el precio de compra.",
};

export function HumanReviewNotice({ review }: { review?: ResearchHumanReview }) {
  if (!review?.human_review_recommended) return null;
  return (
    <div className="notice" aria-label="Revisión humana investigativa">
      <strong>Revisión humana recomendada</strong>
      <ul className="small">
        {review.human_review_reasons.map((reason) => (
          <li key={reason}>{REASONS[reason] ?? reason}</li>
        ))}
      </ul>
      <p className="small muted">No es una señal confirmada ni una conclusión de irregularidad.</p>
    </div>
  );
}
