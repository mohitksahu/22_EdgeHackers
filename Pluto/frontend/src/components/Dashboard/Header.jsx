import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Header({ user, onBack, onNewPlanet }) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  const getUserInitial = () => {
    if (!user) return '?';
    if (user.name) return user.name.charAt(0).toUpperCase();
    if (user.email) return user.email.charAt(0).toUpperCase();
    return '?';
  };

  const handleAvatarClick = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  const handleClickOutside = (e) => {
    if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
      setIsDropdownOpen(false);
    }
  };

  const handleEscapeKey = (e) => {
    if (e.key === 'Escape') {
      setIsDropdownOpen(false);
    }
  };

  useEffect(() => {
    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscapeKey);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, [isDropdownOpen]);

  return (
    <header className="h-16 flex items-center justify-between px-8 border-b border-l border-r border-[var(--card-border,#1f1f2e)] bg-[var(--card-bg,#14141f)]/50">
      {/* Back Button and Logo */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => onBack ? onBack() : navigate('/')}
          className="p-2 rounded-xl hover:bg-[var(--card-bg,#14141f)] transition-all duration-200 text-[var(--secondary-text,#9ca3af)] hover:text-white"
          aria-label="Back to home"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        
        <div className="flex items-center">
          <h1 className="text-2xl font-medium tracking-tight">
            <span className="text-[var(--text-color)]">PLUTO<span className="text-pluto-purple">.</span></span>
          </h1>
        </div>
      </div>

      {/* Right Icons */}
      <div className="flex items-center gap-4">
        {/* New Planet Button */}
        {/* TODO: Implement navigation logic */}
        {/* Clicking this button should: */}
        {/*   1. Save the current workspace state */}
        {/*   2. Navigate to a new empty dashboard instance */}
        <button 
          className="py-2 px-4 rounded-xl bg-pluto-purple hover:bg-pluto-purple-dark text-white text-sm font-medium transition-all duration-200 flex items-center gap-2 shadow-lg shadow-pluto-purple/20 hover:shadow-pluto-purple/40"
          onClick={() => onNewPlanet ? onNewPlanet() : navigate('/newplanet')}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Planet
        </button>

        {/* Search Icon - Hidden for offline mode. Remove 'hidden' class to re-enable for online use */}
        <button 
          className="p-2 rounded-xl hover:bg-[var(--card-bg,#14141f)] transition-all duration-200 hidden"
          aria-label="Search"
        >
          <svg className="w-5 h-5 text-[var(--secondary-text,#9ca3af)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </button>

        {/* User Avatar with Dropdown - Hidden for offline mode. Remove 'hidden' class to re-enable for online use */}
        <div className="relative hidden" ref={dropdownRef}>
          <button 
            onClick={handleAvatarClick}
            className="w-8 h-8 rounded-full bg-gradient-to-br from-pluto-purple to-pluto-purple-dark flex items-center justify-center text-white text-sm font-medium hover:shadow-lg hover:shadow-pluto-purple/20 transition-all duration-200"
            aria-label="User menu"
            aria-expanded={isDropdownOpen}
          >
            {getUserInitial()}
          </button>

          {/* Dropdown Menu */}
          {isDropdownOpen && (
            <div className="absolute right-0 mt-2 w-64 rounded-xl bg-[var(--card-bg,#14141f)]/95 backdrop-blur-glass border border-[var(--card-border,#1f1f2e)] shadow-2xl shadow-black/50 overflow-hidden z-50">
              {user ? (
                <>
                  {/* User Info */}
                  <div className="px-4 py-3 border-b border-[var(--card-border,#1f1f2e)]">
                    <p className="text-sm font-medium text-white truncate">
                      {user.name || 'User'}
                    </p>
                    {user.email && (
                      <p className="text-xs text-[var(--secondary-text,#9ca3af)] truncate mt-1">
                        {user.email}
                      </p>
                    )}
                  </div>

                  {/* Menu Items */}
                  <div className="py-1">
                    <button
                      className="w-full px-4 py-2 text-sm text-[var(--text-color,#e5e7eb)] hover:bg-[var(--card-bg,#14141f)] text-left transition-colors duration-200 cursor-not-allowed opacity-50"
                      disabled
                    >
                      Account settings
                    </button>
                    <button
                      className="w-full px-4 py-2 text-sm text-[var(--text-color,#e5e7eb)] hover:bg-[var(--card-bg,#14141f)] text-left transition-colors duration-200"
                      onClick={() => {
                        setIsDropdownOpen(false);
                        // Backend will handle logout
                      }}
                    >
                      Logout
                    </button>
                  </div>
                </>
              ) : (
                /* Not Signed In State */
                <div className="px-4 py-3">
                  <p className="text-sm text-[var(--secondary-text,#9ca3af)] text-center">
                    Not signed in
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
