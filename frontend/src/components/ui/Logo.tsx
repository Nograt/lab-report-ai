type LogoProps = {
  className?: string;
};

export function LogoMark({ className = "h-9 w-9" }: LogoProps) {
  return (
    <svg
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <path
        d="M9 3.5H25.5L33.5 11.5V32.5C33.5 34.7091 31.7091 36.5 29.5 36.5H9C6.79086 36.5 5 34.7091 5 32.5V7.5C5 5.29086 6.79086 3.5 9 3.5Z"
        fill="#F97316"
      />

      <path
        d="M25.5 3.5V9C25.5 10.3807 26.6193 11.5 28 11.5H33.5L25.5 3.5Z"
        fill="#FDBA74"
      />

      <path
        d="M25.8 14.4C24.25 13.15 22.25 12.5 20.05 12.5C16.35 12.5 13.55 14.3 13.55 17.2C13.55 20 15.75 21.15 19.2 21.85C22.1 22.45 23.05 23 23.05 24.35C23.05 25.75 21.75 26.55 19.65 26.55C17.5 26.55 15.5 25.75 13.85 24.35L11.75 27C13.8 28.85 16.5 29.8 19.5 29.8C23.95 29.8 26.95 27.65 26.95 24.1C26.95 20.95 24.6 19.7 20.95 18.95C18.35 18.4 17.4 17.95 17.4 16.9C17.4 15.9 18.35 15.25 20.15 15.25C21.75 15.25 23.25 15.8 24.55 16.8L25.8 14.4Z"
        fill="white"
      />
    </svg>
  );
}

export function Logo() {
  return (
    <div className="flex items-center">
      <LogoMark />

      <span className="text-lg font-semibold tracking-tight text-neutral-950">
        sprawko
        <span className="text-neutral-400">.pl</span>
      </span>
    </div>
  );
}