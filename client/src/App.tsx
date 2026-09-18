import { useState } from "react";
import Sidebar from "./components/Sidebar";
import LandingPage from "./pages/LandingPage";
import Dashboard from "./pages/Dashboard";
import UncertaintyPage from "./pages/UncertaintyPage";
import ValidationPage from "./pages/ValidationPage";
import GeoAssistPage from "./pages/GeoAssistPage";
import ProjectsPage from "./pages/ProjectsPage";

export type Page =
  | "landing"
  | "dashboard"
  | "new-analysis"
  | "projects"
  | "imagery"
  | "validation"
  | "reports"
  | "geoassist"
  | "settings"
  | "uncertainty";

const APP_PAGES: Page[] = ["dashboard", "new-analysis", "projects", "imagery", "validation", "reports", "geoassist", "settings"];

export default function App() {
  const [page, setPage] = useState<Page>("landing");
  const [objectName, setObjectName] = useState<string | null>(null);

  if (page === "landing") {
    return (
      <div className="size-full">
        <LandingPage onNavigate={setPage} />
      </div>
    );
  }

  const renderPage = () => {
    switch (page) {
      case "dashboard":
      case "new-analysis":
      case "imagery":
      case "reports":
      case "settings":
        return <Dashboard onNavigate={setPage} objectName={objectName} setObjectName={setObjectName} />;
      case "uncertainty":
        return <UncertaintyPage objectName={objectName} />;
      case "validation":
        return <ValidationPage objectName={objectName} />;
      case "geoassist":
        return <GeoAssistPage />;
      case "projects":
        return <ProjectsPage onNavigate={setPage} />;
      default:
        return <Dashboard onNavigate={setPage} objectName={objectName} setObjectName={setObjectName} />;
    }
  };

  return (
    <div className="size-full flex bg-navy-900">
      <Sidebar current={page} onNavigate={setPage} />
      <main className="flex-1 min-w-0 overflow-hidden">
        {renderPage()}
      </main>
    </div>
  );
}
