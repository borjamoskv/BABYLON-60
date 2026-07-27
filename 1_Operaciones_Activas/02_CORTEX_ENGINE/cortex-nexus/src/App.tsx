import { Routes, Route } from 'react-router';
import Dashboard from './pages/Dashboard';
import SubstackReport from './pages/SubstackReport';
import PhotobiologyReport from './pages/PhotobiologyReport';
import { ThemeProvider } from './hooks/useTheme';
import DesignVariations from './components/DesignVariations';

function App() {
  return (
    <ThemeProvider defaultTheme="noir">
      <div className="w-full h-full min-h-screen bg-background text-foreground transition-colors duration-300">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/substack" element={<SubstackReport />} />
          <Route path="/photobiology" element={<PhotobiologyReport />} />
        </Routes>
        <DesignVariations />
      </div>
    </ThemeProvider>
  );
}

export default App;
