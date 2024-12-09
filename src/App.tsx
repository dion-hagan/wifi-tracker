import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import { Card } from './components/ui/card';
import { Map, ListChecks, BarChart3, Settings, Menu, MonitorSmartphone } from 'lucide-react';
import DeviceMap from './components/DeviceMap';
import DeviceList from './components/DeviceList';
import Analytics from './components/Analytics';
import SettingsView from './components/Settings';

const NavLink = ({ to, children }: { to: string; children: React.ReactNode }) => {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      to={to}
      className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md ${
        isActive
          ? 'bg-blue-50 text-blue-700'
          : 'text-gray-600 hover:bg-gray-50'
      }`}
    >
      {children}
    </Link>
  );
};

const App = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navigation = [
    { id: 'map', name: 'Device Map', icon: Map, path: '/map' },
    { id: 'list', name: 'Device List', icon: ListChecks, path: '/list' },
    { id: 'analytics', name: 'Device Analytics', icon: BarChart3, path: '/analytics' },
    { id: 'settings', name: 'Settings', icon: Settings, path: '/settings' }
  ];

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white shadow">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 justify-between">
              <div className="flex">
                <Link to="/map" className="flex flex-shrink-0 items-center">
                  <MonitorSmartphone className="h-8 w-8 text-blue-500" />
                  <span className="ml-2 text-xl font-bold">WiFi Tracker</span>
                </Link>
              </div>

              {/* Mobile menu button */}
              <div className="flex items-center lg:hidden">
                <button
                  onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                  className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
                >
                  <Menu className="h-6 w-6" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col lg:flex-row gap-6">
            {/* Sidebar Navigation */}
            <div className="lg:w-64 flex-shrink-0">
              <Card className="p-2">
                <nav className="space-y-1">
                  {navigation.map((item) => {
                    const Icon = item.icon;
                    return (
                      <NavLink key={item.id} to={item.path}>
                        <Icon className="mr-3 h-5 w-5" />
                        {item.name}
                      </NavLink>
                    );
                  })}
                </nav>
              </Card>
            </div>

            {/* Main Content */}
            <div className="flex-1">
              <Routes>
                <Route path="/map" element={<DeviceMap />} />
                <Route path="/list" element={<DeviceList />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/settings" element={<SettingsView />} />
                <Route path="/" element={<Navigate to="/map" replace />} />
              </Routes>
            </div>
          </div>
        </div>
      </div>
    </Router>
  );
};

export default App;
