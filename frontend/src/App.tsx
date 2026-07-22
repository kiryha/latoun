import { useState } from "react";
import { AssignmentsManager } from "./assignments/AssignmentsManager";
import { Configurator } from "./configurator/Configurator";
import { MaterialsManager } from "./materials/MaterialsManager";

type Tab = "assembly" | "materials" | "assignments";

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("assembly");

  return (
    <div className="app">
      <header className="app-header">
        <nav className="app-tabs" role="tablist" aria-label="Sections">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "assembly"}
            className={`app-tab${activeTab === "assembly" ? " is-active" : ""}`}
            onClick={() => setActiveTab("assembly")}
          >
            Assembly
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "materials"}
            className={`app-tab${activeTab === "materials" ? " is-active" : ""}`}
            onClick={() => setActiveTab("materials")}
          >
            Materials
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "assignments"}
            className={`app-tab${activeTab === "assignments" ? " is-active" : ""}`}
            onClick={() => setActiveTab("assignments")}
          >
            Assignments
          </button>
        </nav>
      </header>

      {activeTab === "assembly" ? (
        <Configurator />
      ) : activeTab === "materials" ? (
        <MaterialsManager />
      ) : (
        <AssignmentsManager />
      )}
    </div>
  );
}
