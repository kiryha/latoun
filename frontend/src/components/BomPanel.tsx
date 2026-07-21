// Prototype BOM table. Clearly labeled as provisional per the brief.

import type { BomLine } from "../types";

interface BomPanelProps {
  bom: BomLine[];
}

export function BomPanel({ bom }: BomPanelProps) {
  return (
    <section className="bom-panel">
      <div className="bom-header">
        <h2>Prototype BOM</h2>
        <span className="badge">Provisional — visible assembly parts only</span>
      </div>
      <table className="bom-table">
        <thead>
          <tr>
            <th>Component</th>
            <th>Code</th>
            <th>Qty</th>
            <th>Material</th>
          </tr>
        </thead>
        <tbody>
          {bom.map((line) => (
            <tr key={line.component_code}>
              <td>{line.display_name}</td>
              <td className="mono">{line.component_code}</td>
              <td>{line.quantity}</td>
              <td className="capitalize">{line.material}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
