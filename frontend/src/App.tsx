import { useState } from "react";
import { AssignmentsManager } from "./assignments/AssignmentsManager";
import { Configurator } from "./configurator/Configurator";
import { GeometryTab } from "./geometry/GeometryTab";
import { MaterialsManager } from "./materials/MaterialsManager";

type Tab = "assembly" | "geometry" | "materials" | "assignments";

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("assembly");
  const [geometryDirty, setGeometryDirty] = useState(false);

  const requestTabChange = (next: Tab) => {
    if (next === activeTab) return;
    if (
      activeTab === "geometry" &&
      geometryDirty &&
      !window.confirm(
        "You have unsaved Geometry manifest changes. Leave this tab anyway?",
      )
    ) {
      return;
    }
    setActiveTab(next);
  };

  return (
    <div className="app">
      <header className="app-header">
        <nav className="app-tabs" role="tablist" aria-label="Sections">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "assembly"}
            className={`app-tab${activeTab === "assembly" ? " is-active" : ""}`}
            onClick={() => requestTabChange("assembly")}
          >
            Assembly
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "geometry"}
            className={`app-tab${activeTab === "geometry" ? " is-active" : ""}`}
            onClick={() => requestTabChange("geometry")}
          >
            Geometry
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "materials"}
            className={`app-tab${activeTab === "materials" ? " is-active" : ""}`}
            onClick={() => requestTabChange("materials")}
          >
            Materials
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "assignments"}
            className={`app-tab${activeTab === "assignments" ? " is-active" : ""}`}
            onClick={() => requestTabChange("assignments")}
          >
            Assignments
          </button>
        </nav>
      </header>

      {activeTab === "assembly" ? (
        <Configurator />
      ) : activeTab === "geometry" ? (
        <GeometryTab onDirtyChange={setGeometryDirty} />
      ) : activeTab === "materials" ? (
        <MaterialsManager />
      ) : (
        <AssignmentsManager />
      )}
    </div>
  );
}
