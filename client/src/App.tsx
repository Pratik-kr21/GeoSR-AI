import { useState } from "react";
import Sidebar from "./components/Sidebar";
import LandingPage from "./pages/LandingPage";
import Dashboard from "./pages/Dashboard";
import UncertaintyPage from "./pages/UncertaintyPage";
import ValidationPage from "./pages/ValidationPage";
import GeoAssistPage from "./pages/GeoAssistPage";
import ProjectsPage from "./pages/ProjectsPage";
import IntelligencePage from "./pages/IntelligencePage";
import ChangeDetectionPage from "./pages/ChangeDetectionPage";
import RiskAnalysisPage from "./pages/RiskAnalysisPage";
import TimelinePage from "./pages/TimelinePage";
import HistoricalComparisonPage from "./pages/HistoricalComparisonPage";
import MultiSensorDataPage from "./pages/MultiSensorDataPage";

export type Page =
  | "landing"
  | "dashboard"
  | "projects"
  | "validation"
  | "geoassist"
  | "uncertainty"
  | "intelligence"
  | "change-detection"
  | "risk-analysis"
  | "timeline"
  | "historical"
  | "sensor-data";

const APP_PAGES: Page[] = ["dashboard", "projects", "validation", "geoassist", "intelligence", "sensor-data", "change-detection", "risk-analysis", "timeline", "historical"];

export default function App() {
  const [page, setPage] = useState<Page>("landing");
  const [objectName, setObjectName] = useState<string | null>(null);
  const [sensorData, setSensorData] = useState<any>(null);

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
        return <Dashboard onNavigate={setPage} objectName={objectName} setObjectName={setObjectName} setSensorData={setSensorData} />;
      case "uncertainty":
        return <UncertaintyPage objectName={objectName} />;
      case "validation":
        return <ValidationPage objectName={objectName} />;
      case "geoassist":
        return <GeoAssistPage />;
      case "projects":
        return <ProjectsPage onNavigate={setPage} />;
      case "intelligence":
        return <IntelligencePage objectName={objectName} onNavigate={setPage} />;
      case "change-detection":
        return <ChangeDetectionPage />;
      case "risk-analysis":
        return <RiskAnalysisPage onNavigate={setPage} />;
      case "timeline":
        return <TimelinePage />;
      case "historical":
        return <HistoricalComparisonPage onNavigate={setPage} />;
      case "sensor-data":
        return <MultiSensorDataPage sensorData={sensorData} objectName={objectName} />;
      default:
        return <Dashboard onNavigate={setPage} objectName={objectName} setObjectName={setObjectName} setSensorData={setSensorData} />;
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
