interface AvailabilityIconProps {
  availability: string | null | undefined;
  className?: string;
  showText?: boolean;
}

export const AvailabilityIcon = ({ availability, className = "", showText = false }: AvailabilityIconProps) => {
  if (!availability) return null;

  const key = availability.toLowerCase();

  if (key === "available") {
    return (
      <span
        title="Available"
        className={`inline-flex items-center gap-1.5 flex-shrink-0 ${className}`}
      >
        <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-green-500">
          <svg viewBox="0 0 12 12" className="w-3 h-3" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="2,6 5,9 10,3" />
          </svg>
        </span>
        {showText && <span className="text-sm font-semibold text-green-600">Available</span>}
      </span>
    );
  }

  if (key === "uncertain") {
    return (
      <span
        title="Uncertain"
        className={`inline-flex items-center gap-1.5 flex-shrink-0 ${className}`}
      >
        <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-yellow-400">
          <svg viewBox="0 0 12 12" className="w-3 h-3" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round">
            <line x1="2" y1="6" x2="10" y2="6" />
          </svg>
        </span>
        {showText && <span className="text-sm font-semibold text-yellow-600">Uncertain</span>}
      </span>
    );
  }

  if (key === "injured") {
    return (
      <span
        title="Injured"
        className={`inline-flex items-center gap-1.5 flex-shrink-0 ${className}`}
      >
        <svg viewBox="0 0 20 20" className="w-5 h-5" fill="red">
          {/* Vertical bar of the cross */}
          <rect x="8" y="2" width="4" height="16" rx="1" />
          {/* Horizontal bar of the cross */}
          <rect x="2" y="8" width="16" height="4" rx="1" />
        </svg>
        {showText && <span className="text-sm font-semibold text-red-600">Injured</span>}
      </span>
    );
  }

  if (key === "suspended") {
    return (
      <span
        title="Suspended"
        className={`inline-flex items-center gap-1.5 flex-shrink-0 ${className}`}
      >
        {/* Red card: tall rectangular card shape */}
        <span className="block w-[14px] h-[20px] rounded-[3px] bg-red-600" />
        {showText && <span className="text-sm font-semibold text-red-600">Suspended</span>}
      </span>
    );
  }

  return null;
};
