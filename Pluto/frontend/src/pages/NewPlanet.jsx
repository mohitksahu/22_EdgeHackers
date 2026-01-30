import React, { useEffect, useRef, useState } from "react";
import "../styles/NewPlanet.css";
import { useNavigate } from "react-router-dom";

const NewPlanet = () => {
  const navigate = useNavigate();
  const sectionsRef = useRef([]);
  const [planetHistory, setPlanetHistory] = useState([]);
  const [openMenuId, setOpenMenuId] = useState(null);
  const [renamingPlanet, setRenamingPlanet] = useState(null);
  const [newName, setNewName] = useState("");
  const [renameError, setRenameError] = useState("");
  const [showAllHistory, setShowAllHistory] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    // Load planet history from localStorage
    const history = JSON.parse(localStorage.getItem('planetHistory') || '[]');
    setPlanetHistory(history);

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
          }
        });
      },
      { threshold: 0.1 }
    );

    sectionsRef.current.forEach((section) => {
      if (section) observer.observe(section);
    });

    // Handle clicks outside menu to close it
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setOpenMenuId(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      observer.disconnect();
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const addToRefs = (el) => {
    if (el && !sectionsRef.current.includes(el)) {
      sectionsRef.current.push(el);
    }
  };

  const handlePlanetClick = (planet) => {
    // Navigate to dashboard with planet data
    navigate("/dashboard", { state: { loadPlanet: planet } });
  };

  const handleMenuClick = (e, planetId) => {
    e.stopPropagation();
    setOpenMenuId(openMenuId === planetId ? null : planetId);
  };

  const handleDeletePlanet = (planetId) => {
    const updatedHistory = planetHistory.filter(planet => planet.id !== planetId);
    setPlanetHistory(updatedHistory);
    localStorage.setItem('planetHistory', JSON.stringify(updatedHistory));
    setOpenMenuId(null);
  };

  const handleRenamePlanet = (planet) => {
    setRenamingPlanet(planet);
    setNewName(planet.name || "");
    setRenameError("");
    setOpenMenuId(null);
  };

  const handleRenameSubmit = () => {
    const trimmedName = newName.trim();
    if (!trimmedName) {
      setRenameError('Planet name cannot be empty');
      return;
    }

    // Check for duplicate names (excluding the current planet)
    const existingPlanet = planetHistory.find(planet => 
      planet.name === trimmedName && planet.id !== renamingPlanet.id
    );
    if (existingPlanet) {
      setRenameError('A planet with this name already exists. Please choose a different name.');
      return;
    }

    const updatedHistory = planetHistory.map(planet =>
      planet.id === renamingPlanet.id
        ? { ...planet, name: trimmedName }
        : planet
    );
    setPlanetHistory(updatedHistory);
    localStorage.setItem('planetHistory', JSON.stringify(updatedHistory));
    setRenamingPlanet(null);
    setNewName("");
    setRenameError("");
  };

  const handleRenameCancel = () => {
    setRenamingPlanet(null);
    setNewName("");
    setRenameError("");
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
  };

  return (
    <div className="new-planet">
      {/* Header */}
      <div className="new-planet-header fade-in" ref={addToRefs}>
        <h2>Planet History</h2>
      </div>

      {/* Cards */}
      <div className="planet-grid fade-in" ref={addToRefs}>
        {/* Create New Workspace */}
        <div
          className="planet-card create-planet"
          onClick={() => navigate("/dashboard")}
        >
          <div className="plus-circle">+</div>
          <p>New Workspace</p>
        </div>

        {/* Planet History */}
        {(showAllHistory ? planetHistory : planetHistory.slice(0, 6)).map((planet, index) => (
          <div
            className="planet-card planet-history-card"
            key={planet.id}
            onClick={() => handlePlanetClick(planet)}
          >
            <div className="card-top">
              <div className="initials">🌍</div>
              <div className="menu-container" ref={openMenuId === planet.id ? menuRef : null}>
                <button
                  className="menu-button"
                  onClick={(e) => handleMenuClick(e, planet.id)}
                >
                  ⋮
                </button>
                {openMenuId === planet.id && (
                  <div className="dropdown-menu">
                    <button
                      className="dropdown-item"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRenamePlanet(planet);
                      }}
                    >
                      ✏️ Rename
                    </button>
                    <button
                      className="dropdown-item delete"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeletePlanet(planet.id);
                      }}
                    >
                      🗑️ Delete
                    </button>
                  </div>
                )}
              </div>
            </div>
            {renamingPlanet?.id === planet.id ? (
              <div className="rename-input-container">
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleRenameSubmit();
                    if (e.key === 'Escape') handleRenameCancel();
                  }}
                  onClick={(e) => e.stopPropagation()}
                  className="rename-input"
                  autoFocus
                />
                {renameError && (
                  <p className="text-red-500 text-sm mt-1">{renameError}</p>
                )}
                <div className="rename-actions">
                  <button
                    className="rename-btn save"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRenameSubmit();
                    }}
                    disabled={!newName.trim()}
                  >
                    ✓
                  </button>
                  <button
                    className="rename-btn cancel"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRenameCancel();
                    }}
                  >
                    ✕
                  </button>
                </div>
              </div>
            ) : (
              <h3>{planet.name || `Untitled Planet ${index + 1}`}</h3>
            )}
            <span className="meta">
              {formatDate(planet.timestamp)} · {planet.sources} source{planet.sources !== 1 ? 's' : ''} · {planet.messages.length} message{planet.messages.length !== 1 ? 's' : ''}
            </span>
          </div>
        ))}
      </div>
      {planetHistory.length > 6 && (
        <div className="show-more-container" style={{ textAlign: 'center', marginTop: '20px' }}>
          <button 
            className="see-all-btn" 
            onClick={() => setShowAllHistory(!showAllHistory)}
          >
            {showAllHistory ? 'Show Less History' : 'Show More History'} →
          </button>
        </div>
      )}
    </div>
  );
};

export default NewPlanet;
