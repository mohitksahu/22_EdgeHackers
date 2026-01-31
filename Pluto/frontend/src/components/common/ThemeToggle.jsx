import { useTheme } from '../../context/ThemeContext';
import './ThemeToggle.css';

const ThemeToggle = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      className="theme-toggle"
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
    >
      <div className="toggle-slider">
        {theme === 'dark' ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" fill="none"/>
            <circle cx="12" cy="12" r="6" stroke="currentColor" strokeWidth="1" fill="none"/>
            <circle cx="12" cy="12" r="2" fill="currentColor"/>
          </svg>
        ) : (
          <span className="toggle-text">PLUTO</span>
        )}
      </div>
    </button>
  );
};

export default ThemeToggle;