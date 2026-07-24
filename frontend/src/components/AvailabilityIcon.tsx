interface AvailabilityIconProps {
  availability: string | null | undefined;
  className?: string;
}

export const AvailabilityIcon = ({ availability, className = "" }: AvailabilityIconProps) => {
  if (!availability) return null;

  const key = availability.toLowerCase();

  if (key === "available") {
    return (
      <span
        title="Available"
        className={`inline-flex items-center justify-center w-5 h-5 rounded-full bg-green-500 flex-shrink-0 ${className}`}
      >
        <svg viewBox="0 0 12 12" className="w-3 h-3" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="2,6 5,9 10,3" />
        </svg>
      </span>
    );
  }

  if (key === "uncertain") {
    return (
      <span
        title="Uncertain"
        className={`inline-flex items-center justify-center w-5 h-5 rounded-full bg-yellow-400 flex-shrink-0 ${className}`}
      >
        <svg viewBox="0 0 12 12" className="w-3 h-3" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round">
          <line x1="2" y1="6" x2="10" y2="6" />
        </svg>
      </span>
    );
  }

  if (key === "suspended" || key === "injured") {
    const label = key === "suspended" ? "Suspended" : "Injured";
    return (
      <span
        title={label}
        className={`inline-flex items-center justify-center flex-shrink-0 ${className}`}
      >
        <span className="block w-3.5 h-5 rounded-sm bg-red-600" />
      </span>
    );
  }

  return null;
};
