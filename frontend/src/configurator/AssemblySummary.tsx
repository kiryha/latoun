import type { AssemblyConfiguration, ModuleTypeOption } from "./assemblyTypes";
import { buildAssemblyStateName } from "./assemblyStateNameService";

interface AssemblySummaryProps {
  configuration: AssemblyConfiguration;
  moduleOptions: ModuleTypeOption[];
  finishDisplayName: string;
}

function moduleDisplayName(
  code: string,
  moduleOptions: ModuleTypeOption[],
): string {
  return (
    moduleOptions.find((option) => option.code === code)?.displayName ?? code
  );
}

export function AssemblySummary({
  configuration,
  moduleOptions,
  finishDisplayName,
}: AssemblySummaryProps) {
  const stateName = buildAssemblyStateName(configuration);

  return (
    <section className="summary">
      <h3>Assembly</h3>
      <dl>
        <div>
          <dt>Gang count</dt>
          <dd>{configuration.gangCount}</dd>
        </div>
        {[...configuration.slots]
          .sort((a, b) => a.slotNumber - b.slotNumber)
          .map((slot) => (
            <div key={slot.slotNumber}>
              <dt>Slot {slot.slotNumber}</dt>
              <dd>
                {moduleDisplayName(slot.moduleTypeCode, moduleOptions)}
              </dd>
            </div>
          ))}
        <div>
          <dt>Finish</dt>
          <dd>{finishDisplayName}</dd>
        </div>
        <div>
          <dt>State name</dt>
          <dd className="mono">{stateName}</dd>
        </div>
      </dl>
    </section>
  );
}
