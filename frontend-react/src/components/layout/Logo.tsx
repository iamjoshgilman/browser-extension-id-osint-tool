import React from 'react';

interface LogoProps {
  size?: number;
  className?: string;
}

export const Logo: React.FC<LogoProps> = ({ size = 32, className = '' }) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 32 32"
      fill="none"
      width={size}
      height={size}
      className={className}
      aria-label="Extension Intel Logo"
    >
      {/* Shield outline */}
      <path
        d="M16 3L7 6v7c0 5.5 3.8 10.7 9 12 5.2-1.3 9-6.5 9-12V6l-9-3z"
        stroke="#58a6ff"
        strokeWidth="2"
        strokeLinejoin="round"
      />

      {/* Magnifying glass */}
      <circle
        cx="18.5"
        cy="15.5"
        r="4.5"
        stroke="#58a6ff"
        strokeWidth="1.8"
        fill="none"
      />
      <line
        x1="15"
        y1="19"
        x2="12"
        y2="22"
        stroke="#58a6ff"
        strokeWidth="1.8"
        strokeLinecap="round"
      />

      {/* Small puzzle piece accent inside shield (subtle) */}
      <path
        d="M13 11h-2v2h2c.5 0 1 .5 1 1v2h2v-2c0-1.7-1.3-3-3-3z"
        fill="#3fb950"
        opacity="0.6"
      />
    </svg>
  );
};
