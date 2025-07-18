import React from 'react';

const NeuralBackground = () => {
  return (
    <div className="fixed inset-0 w-full h-full -z-10">
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-neural-900 via-neural-800 to-neural-900 animate-gradient-xy"></div>
      
      {/* Floating orbs */}
      <div className="absolute inset-0 overflow-hidden">
        {[...Array(8)].map((_, i) => (
          <div
            key={i}
            className={`floating-orb w-${4 + i % 3} h-${4 + i % 3} bg-accent-${500 + (i % 2) * 100} opacity-${10 + i % 20}`}
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${i * 0.5}s`,
              animationDuration: `${6 + i % 4}s`
            }}
          />
        ))}
      </div>
      
      {/* Neural network grid */}
      <div className="absolute inset-0 opacity-5">
        <svg width="100%" height="100%" className="animate-pulse-slow">
          <defs>
            <pattern id="neural-grid" width="100" height="100" patternUnits="userSpaceOnUse">
              <circle cx="50" cy="50" r="2" fill="#e935ff" opacity="0.3"/>
              <line x1="0" y1="50" x2="100" y2="50" stroke="#e935ff" strokeWidth="1" opacity="0.1"/>
              <line x1="50" y1="0" x2="50" y2="100" stroke="#e935ff" strokeWidth="1" opacity="0.1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#neural-grid)" />
        </svg>
      </div>
      
      {/* Overlay gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-neural-900/90 via-neural-900/50 to-neural-800/90 pointer-events-none" />
    </div>
  );
};

export default NeuralBackground;