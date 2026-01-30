import { useRef, useEffect } from 'react';
import './SpotlightCard.css';

const SpotlightCard = ({ children, className = '' }) => {
  const divRef = useRef(null);

  useEffect(() => {
    const updateSpotlightColor = () => {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      const spotlightColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(99, 102, 241, 0.15)';
      divRef.current?.style.setProperty('--spotlight-color', spotlightColor);
    };

    // Set initial color
    updateSpotlightColor();

    // Listen for theme changes
    const observer = new MutationObserver(updateSpotlightColor);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme']
    });

    return () => observer.disconnect();
  }, []);

  const handleMouseMove = e => {
    const rect = divRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    divRef.current.style.setProperty('--mouse-x', `${x}px`);
    divRef.current.style.setProperty('--mouse-y', `${y}px`);
  };

  return (
    <div ref={divRef} onMouseMove={handleMouseMove} className={`card-spotlight ${className}`}>
      {children}
    </div>
  );
};

export default SpotlightCard;