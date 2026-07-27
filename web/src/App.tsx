import { useState } from 'react';
import { LayoutDashboard, Target, Users, CalendarClock, Blocks, Settings } from 'lucide-react';
import { Dashboard } from './components/Dashboard';
import { GoalMode } from './components/GoalMode';
import { SwarmOverview } from './components/SwarmOverview';
import { ScheduledTasks } from './components/ScheduledTasks';
import { FinancialPlugins } from './components/FinancialPlugins';
import './App.css';

type View = 'dashboard' | 'goal' | 'swarm' | 'scheduled' | 'plugins';

function App() {
  const [currentView, setCurrentView] = useState<View>('dashboard');

  const renderView = () => {
    switch (currentView) {
      case 'dashboard': return <Dashboard />;
      case 'goal': return <GoalMode />;
      case 'swarm': return <SwarmOverview />;
      case 'scheduled': return <ScheduledTasks />;
      case 'plugins': return <FinancialPlugins />;
      default: return <Dashboard />;
    }
  };

  return (
    <div className="dashboard-layout">
      {/* Sidebar Navigation */}
      <nav className="sidebar">
        <div className="brand">
          <h1>BABYLON-60</h1>
        </div>
        
        <div className="nav-links" style={{ flex: 1 }}>
          <a 
            className={`nav-item ${currentView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentView('dashboard')}
          >
            <LayoutDashboard className="nav-icon" /> Dashboard
          </a>
          
          <a 
            className={`nav-item ${currentView === 'goal' ? 'active' : ''}`}
            onClick={() => setCurrentView('goal')}
          >
            <Target className="nav-icon" /> Goal Mode
          </a>

          <a 
            className={`nav-item ${currentView === 'swarm' ? 'active' : ''}`}
            onClick={() => setCurrentView('swarm')}
          >
            <Users className="nav-icon" /> Swarm Orchestrator
          </a>

          <a 
            className={`nav-item ${currentView === 'scheduled' ? 'active' : ''}`}
            onClick={() => setCurrentView('scheduled')}
          >
            <CalendarClock className="nav-icon" /> Scheduled Tasks
          </a>

          <a 
            className={`nav-item ${currentView === 'plugins' ? 'active' : ''}`}
            onClick={() => setCurrentView('plugins')}
          >
            <Blocks className="nav-icon" /> Financial Plugins
          </a>
        </div>

        <div className="nav-links">
          <a className="nav-item">
            <Settings className="nav-icon" /> Settings
          </a>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="main-content">
        {renderView()}
      </main>
    </div>
  );
}

export default App;
