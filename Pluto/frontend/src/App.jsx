import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Query from './pages/Query';
import Ingest from './pages/Ingest';
import Results from './pages/Results';
import NotFound from './pages/NotFound';
import Login from './pages/Login';
import Signup from './pages/Signup';
import About from './pages/about';
import NewPlanet from './pages/NewPlanet';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <div className="min-h-screen w-full overflow-x-hidden">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/about" element={<About />} />
            <Route path="/query" element={<Query />} />
            <Route path="/ingest" element={<Ingest />} />
            <Route path="/results" element={<Results />} />
            <Route path="/newplanet" element={<NewPlanet />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
      </div>
    </Router>
    </ThemeProvider>
  );
}

export default App;
