import { LoveRealityProDashboard } from "./pages/LoveRealityProDashboard";
import { sampleReportData } from "./sampleData";

export default function App() {
  return (
    <div className="min-h-screen py-4">
      <LoveRealityProDashboard data={sampleReportData} />
    </div>
  );
}
