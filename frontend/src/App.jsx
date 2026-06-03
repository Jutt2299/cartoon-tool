import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import Home from "./pages/Home";
import History from "./pages/History";
import Settings from "./pages/Settings";
import Status from "./pages/Status";

function App() {
  return (
    <Router>
      <div className="flex min-h-screen bg-[#0B0C10] text-gray-100 font-sans">
        <Sidebar />
        <main className="flex-1 ml-64 flex flex-col h-screen overflow-hidden">
          <Header />
          <div className="flex-1 overflow-y-auto p-8">
            <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/history" element={<History />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/status" element={<Status />} />
          </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;