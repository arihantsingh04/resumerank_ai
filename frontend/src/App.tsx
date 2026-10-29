import { Navigate, Route, Routes } from "react-router-dom";
import Check from "./pages/Check";
import Landing from "./pages/Landing";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/check" element={<Check />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
