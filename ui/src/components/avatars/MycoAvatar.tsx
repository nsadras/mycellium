import type { AvatarProps } from './index';

export default function MycoAvatar({ activity }: AvatarProps) {
  // Classes for animations based on the activity state
  let mascotClass = "animate-slow-bob"; // Idle uses slow, subtle bobbing
  if (activity === 'listening') mascotClass = "animate-bob"; // Listening uses more apparent bobbing
  else if (activity === 'thinking') mascotClass = "animate-ponder";
  else if (activity === 'dreaming') mascotClass = "animate-sleep";

  return (
    <svg
      viewBox="14 10 132 132"
      width="100%"
      height="100%"
      xmlns="http://www.w3.org/2000/svg"
      className="select-none"
    >
      <defs>
        <linearGradient id="capGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#a3bcb0" />
          <stop offset="100%" stopColor="#7e9c8e" />
        </linearGradient>
        <linearGradient id="underCapGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#4d665a" />
          <stop offset="100%" stopColor="#3d5248" />
        </linearGradient>
        <linearGradient id="bodyGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#faf8f2" />
          <stop offset="100%" stopColor="#e9e5d4" />
        </linearGradient>
        <linearGradient id="bodyShadowGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#ded9c3" stopOpacity="0.8" />
          <stop offset="100%" stopColor="#cfc9af" stopOpacity="0.2" />
        </linearGradient>
        <radialGradient id="dreamGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#10b981" stopOpacity="0.7" />
          <stop offset="60%" stopColor="#10b981" stopOpacity="0.25" />
          <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="decayGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#a78bfa" stopOpacity="0.6" />
          <stop offset="70%" stopColor="#a78bfa" stopOpacity="0.15" />
          <stop offset="100%" stopColor="#a78bfa" stopOpacity="0" />
        </radialGradient>
      </defs>

      <style>{`
        @keyframes bob {
          0% { transform: translateY(1px); }
          100% { transform: translateY(-5px); }
        }
        .animate-bob {
          animation: bob 1.6s ease-in-out infinite alternate;
        }

        @keyframes slow-bob {
          0% { transform: translateY(0.5px); }
          100% { transform: translateY(-2px); }
        }
        .animate-slow-bob {
          animation: slow-bob 3.2s ease-in-out infinite alternate;
        }

        @keyframes blink {
          0%, 96%, 100% { transform: scaleY(1); }
          98% { transform: scaleY(0.1); }
        }
        .blink-eye {
          animation: blink 4.2s infinite;
        }
        .left-eye {
          transform-origin: 68.5px 94.5px;
        }
        .right-eye {
          transform-origin: 91.5px 94.5px;
        }

        @keyframes sleep-pulse {
          0% { transform: scale(1) translateY(1px); opacity: 0.95; }
          100% { transform: scale(0.97) translateY(3px); opacity: 0.85; }
        }
        .animate-sleep {
          animation: sleep-pulse 2.5s ease-in-out infinite alternate;
          transform-origin: 80px 130px;
        }

        @keyframes breathe-glow {
          0% { transform: scale(0.9) translateY(0px); opacity: 0.6; }
          100% { transform: scale(1.1) translateY(-1px); opacity: 0.95; }
        }
        .animate-glow {
          animation: breathe-glow 2.5s ease-in-out infinite alternate;
          transform-origin: 80px 132px;
        }

        @keyframes float-zzz {
          0% { transform: translate(0px, 5px) scale(0.6); opacity: 0; }
          30% { opacity: 0.8; }
          100% { transform: translate(10px, -20px) scale(1.1); opacity: 0; }
        }
        .zzz-1 { animation: float-zzz 3s ease-in-out infinite; transform-origin: 114px 60px; }
        .zzz-2 { animation: float-zzz 3s ease-in-out infinite 1s; transform-origin: 122px 46px; }
        .zzz-3 { animation: float-zzz 3s ease-in-out infinite 2s; transform-origin: 132px 32px; }

        @keyframes float-log {
          0% { transform: translateY(4px); opacity: 0; }
          40% { opacity: 0.8; }
          100% { transform: translateY(-10px); opacity: 0; }
        }
        .log-line-1 { animation: float-log 1.5s ease-in-out infinite; }
        .log-line-2 { animation: float-log 1.5s ease-in-out infinite 0.75s; }

        @keyframes sparkle-glow {
          0% { transform: scale(0.85); opacity: 0.5; }
          100% { transform: scale(1.15); opacity: 1; }
        }

        @keyframes wave-arm {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(-20deg); }
        }
        .animate-wave {
          animation: wave-arm 0.35s ease-in-out infinite alternate;
          transform-origin: 47px 88px;
        }

        @keyframes ponder {
          0% { transform: rotate(-3deg); }
          100% { transform: rotate(3deg); }
        }
        .animate-ponder {
          animation: ponder 1.5s ease-in-out infinite alternate;
          transform-origin: 80px 130px;
        }

        @keyframes shake-bubble {
          0% { transform: translate(0px, 0px) scale(0.98); }
          100% { transform: translate(1px, -2px) scale(1.02); }
        }
        .animate-bubble {
          animation: shake-bubble 0.6s ease-in-out infinite alternate;
          transform-origin: 114px 46px;
        }

        @keyframes pulse-red {
          0% { opacity: 0.3; }
          100% { opacity: 0.85; }
        }
        .error-glow {
          animation: pulse-red 0.8s ease-in-out infinite alternate;
        }
      `}</style>

      {/* 1. BACKGROUND EFFECT PLANES */}
      {activity === 'dreaming' && (
        <ellipse cx="80" cy="132" rx="50" ry="15" fill="url(#dreamGlow)" className="animate-glow" />
      )}
      {activity === 'decaying' && (
        <ellipse cx="80" cy="132" rx="45" ry="12" fill="url(#decayGlow)" className="animate-glow" />
      )}
      {activity === 'error' && (
        <ellipse cx="80" cy="132" rx="48" ry="14" fill="#ef4444" opacity="0.3" className="animate-glow" />
      )}

      {/* 2. ERROR SHADOW AURA */}
      {activity === 'error' && (
        <g opacity="0.8" className="error-glow">
          <path d="M 20,70 C 20,32 45,18 80,18 C 115,18 140,32 140,70 C 140,84 115,88 80,88 C 45,88 20,84 20,70 Z" fill="none" stroke="#ef4444" strokeWidth="6" filter="blur(2px)" />
          <path d="M 50,75 C 50,110 56,128 65,128 C 72,128 74,120 80,120 C 86,120 88,128 95,128 C 104,128 110,110 110,75 Z" fill="none" stroke="#ef4444" strokeWidth="6" filter="blur(2px)" />
        </g>
      )}

      {/* 3. MASCOT BODY GROUP (Bobs, Waddles, or Sleep-Pulses) */}
      <g className={mascotClass}>
        {/* A. Body Shape */}
        <path
          d="M 50,75 C 50,110 56,128 65,128 C 72,128 74,120 80,120 C 86,120 88,128 95,128 C 104,128 110,110 110,75 Z"
          fill="url(#bodyGrad)"
        />

        {/* B. Shadow on Body immediately below Cap */}
        <path
          d="M 50,75 C 60,82 100,82 110,75 C 110,77 100,83 80,83 C 60,83 50,77 50,75 Z"
          fill="url(#bodyShadowGrad)"
        />

        {/* C. Blush */}
        {activity !== 'dreaming' && activity !== 'decaying' && (
          <g>
            <ellipse cx="60" cy="97" rx="5.5" ry="3.5" fill={activity === 'error' ? "#ef4444" : "#e8a9a9"} opacity={activity === 'error' ? 0.35 : 0.5} />
            <ellipse cx="100" cy="97" rx="5.5" ry="3.5" fill={activity === 'error' ? "#ef4444" : "#e8a9a9"} opacity={activity === 'error' ? 0.35 : 0.5} />
          </g>
        )}

        {/* D. Eyes */}
        {activity === 'dreaming' ? (
          // Sleepy / closed eyes (curved down)
          <g>
            <path d="M 64,93 Q 68.5,97 73,93" stroke="#2c3531" strokeWidth="2.5" strokeLinecap="round" fill="none" />
            <path d="M 87,93 Q 91.5,97 96,93" stroke="#2c3531" strokeWidth="2.5" strokeLinecap="round" fill="none" />
          </g>
        ) : activity === 'responding' ? (
          // Happy / smiling eyes (curved up)
          <g>
            <path d="M 64,95 Q 68.5,90 73,95" stroke="#2c3531" strokeWidth="2.5" strokeLinecap="round" fill="none" />
            <path d="M 87,95 Q 91.5,90 96,95" stroke="#2c3531" strokeWidth="2.5" strokeLinecap="round" fill="none" />
          </g>
        ) : activity === 'error' ? (
          // Worried / sad eyes and eyebrows
          <g>
            <path d="M 63,85 L 70,88" stroke="#2c3531" strokeWidth="2.2" strokeLinecap="round" fill="none" />
            <path d="M 97,85 L 90,88" stroke="#2c3531" strokeWidth="2.2" strokeLinecap="round" fill="none" />
            <circle cx="68.5" cy="94.5" r="4.5" fill="#2c3531" />
            <circle cx="91.5" cy="94.5" r="4.5" fill="#2c3531" />
            <circle cx="69.5" cy="93.5" r="1.2" fill="#ffffff" />
            <circle cx="92.5" cy="93.5" r="1.2" fill="#ffffff" />
          </g>
        ) : (
          // Normal vertical pill eyes
          <g>
            <rect x="66" y="90" width="5" height="9" rx="2.5" fill="#2c3531" className="blink-eye left-eye" />
            <rect x="89" y="90" width="5" height="9" rx="2.5" fill="#2c3531" className="blink-eye right-eye" />
          </g>
        )}

        {/* E. Mouth */}
        {activity === 'responding' ? (
          // Happy open mouth
          <path d="M 76,96 Q 80,102 84,96 Z" fill="#2c3531" />
        ) : activity === 'thinking' ? (
          // Confused / o-mouth
          <circle cx="80" cy="98" r="2.5" fill="#2c3531" />
        ) : activity === 'error' ? (
          // Sad frown
          <path d="M 77,100 Q 80,97 83,100" stroke="#2c3531" strokeWidth="1.8" strokeLinecap="round" fill="none" />
        ) : (
          // Standard small smile
          <path d="M 78,98 Q 80,100 82,98" stroke="#2c3531" strokeWidth="1.8" strokeLinecap="round" fill="none" />
        )}

        {/* F. Cap Crevice (Shadow) */}
        <path
          d="M 24,70 C 24,82 45,86 80,86 C 115,86 136,82 136,70 C 136,70 115,74 80,74 C 45,74 24,70 24,70 Z"
          fill="url(#underCapGrad)"
        />

        {/* G. Cap Shape */}
        <path
          d="M 20,70 C 20,32 45,18 80,18 C 115,18 140,32 140,70 C 140,84 115,88 80,88 C 45,88 20,84 20,70 Z"
          fill="url(#capGrad)"
        />

        {/* H. Arms & Accessories */}
        {activity === 'responding' ? (
          // Happy waving arm pose
          <g>
            {/* Left waving arm (chubby, overlapped) */}
            <path
              d="M 54,93 C 34,86 28,72 30,64 C 35,62 43,76 54,84 Z"
              fill="url(#bodyGrad)"
              className="animate-wave"
            />
            {/* Right normal arm (chubby, overlapped) */}
            <path
              d="M 106,91 C 122,91 126,97 126,103 C 126,110 120,111 106,107 Z"
              fill="url(#bodyGrad)"
            />
          </g>
        ) : activity === 'thinking' ? (
          // Thinking scratching arm pose
          <g>
            {/* Left scratching arm (chubby, overlapped) */}
            <path
              d="M 54,93 C 36,86 34,70 44,68 C 50,67 52,78 54,85 Z"
              fill="url(#bodyGrad)"
            />
            {/* Right normal arm (chubby, overlapped) */}
            <path
              d="M 106,91 C 122,91 126,97 126,103 C 126,110 120,111 106,107 Z"
              fill="url(#bodyGrad)"
            />
          </g>
        ) : (activity === 'flushing' || activity === 'tool_calling') ? (
          // Logging data with clipboard
          <g>
            {/* Clipboard and pages underneath */}
            <g transform="translate(0, 4)">
              {/* Board */}
              <rect x="34" y="86" width="22" height="28" rx="2.5" fill="#3d5248" stroke="#faf8f2" strokeWidth="1" />
              {/* Clip */}
              <rect x="41" y="82" width="8" height="4" rx="1" fill="#a3bcb0" />
              {/* Paper */}
              <rect x="37" y="89" width="16" height="22" rx="1" fill="#faf8f2" />
              {/* Lines */}
              <line x1="40" y1="93" x2="50" y2="93" stroke="#e9e5d4" strokeWidth="1.2" strokeLinecap="round" />
              <line x1="40" y1="98" x2="48" y2="98" stroke="#e9e5d4" strokeWidth="1.2" strokeLinecap="round" />
              <line x1="40" y1="103" x2="46" y2="103" stroke="#e9e5d4" strokeWidth="1.2" strokeLinecap="round" />
            </g>

            {/* Left holding clipboard arm (chubby, overlapped) */}
            <path
              d="M 54,94 C 41,94 36,98 36,104 C 36,110 41,110 54,106 Z"
              fill="url(#bodyGrad)"
            />

            {/* Right arm holding pencil (chubby, overlapped) */}
            <path
              d="M 106,91 C 94,93 82,99 76,96 C 74,99 82,107 106,103 Z"
              fill="url(#bodyGrad)"
            />
            {/* Tiny pencil */}
            <polygon points="77,101 73,100 74,103" fill="#fbbf24" />
          </g>
        ) : activity === 'reconsolidating' ? (
          // Holding glowing wiki page/book
          <g>
            {/* Left normal arm (chubby, overlapped) */}
            <path
              d="M 54,91 C 38,91 34,97 34,103 C 34,110 40,111 54,107 Z"
              fill="url(#bodyGrad)"
            />

            {/* Glowing book */}
            <g transform="translate(2, 4)">
              {/* Book */}
              <rect x="114" y="62" width="20" height="26" rx="2" fill="#3d5248" stroke="#faf8f2" strokeWidth="1" />
              {/* Gold star symbol */}
              <polygon points="124,72 125,75 128,75 126,77 127,80 124,78 121,80 122,77 120,75 123,75" fill="#fbbf24" />
              {/* Sparkles */}
              <path d="M 110,58 L 111.5,60.5 L 114,60.5 L 112,62 L 113,64.5 L 110,63 L 107,64.5 L 108,62 L 106,60.5 L 108.5,60.5 Z" fill="#fbbf24" opacity="0.8" style={{ animation: "sparkle-glow 1.5s infinite alternate" }} />
              <path d="M 134,56 L 135,58 L 137,58 L 135,59.5 L 136,62 L 134,60.5 L 132,62 L 133,59.5 L 131,58 L 133,58 Z" fill="#fbbf24" opacity="0.8" style={{ animation: "sparkle-glow 1.5s infinite alternate 0.75s" }} />
            </g>

            {/* Right arm holding the book up (chubby, overlapped) */}
            <path
              d="M 106,91 C 120,78 128,74 130,78 C 130,83 120,95 106,95 Z"
              fill="url(#bodyGrad)"
            />
          </g>
        ) : (
          // Default normal arm poses (chubby, overlapped)
          <g>
            {/* Left Arm (chubby, overlapped) */}
            <path
              d="M 54,91 C 38,91 34,97 34,103 C 34,110 40,111 54,107 Z"
              fill="url(#bodyGrad)"
            />
            {/* Right Arm (chubby, overlapped) */}
            <path
              d="M 106,91 C 122,91 126,97 126,103 C 126,110 120,111 106,107 Z"
              fill="url(#bodyGrad)"
            />
          </g>
        )}
      </g>

      {/* 4. OVERLAY ACCESSORIES (independent of body bobbing) */}
      {activity === 'dreaming' && (
        <g opacity="0.8">
          <text x="114" y="60" fontSize="11" fontFamily="Arial, sans-serif" fontWeight="bold" fill="#7e9c8e" className="zzz-1">z</text>
          <text x="122" y="46" fontSize="15" fontFamily="Arial, sans-serif" fontWeight="bold" fill="#7e9c8e" className="zzz-2">Z</text>
          <text x="132" y="32" fontSize="20" fontFamily="Arial, sans-serif" fontWeight="bold" fill="#7e9c8e" className="zzz-3">Z</text>
        </g>
      )}

      {activity === 'thinking' && (
        <g className="animate-bubble">
          <circle cx="108" cy="52" r="3" fill="#7e9c8e" />
          <circle cx="114" cy="46" r="4.5" fill="#7e9c8e" />
          <circle cx="128" cy="34" r="13" fill="#7e9c8e" />
          <text x="128" y="39" fontFamily="Arial, sans-serif" fontWeight="bold" fontSize="16" fill="#faf8f2" textAnchor="middle">?</text>
        </g>
      )}

      {activity === 'error' && (
        <g className="animate-bubble">
          <circle cx="110" cy="52" r="3.5" fill="#ef4444" />
          <circle cx="117" cy="45" r="5" fill="#ef4444" />
          <circle cx="130" cy="32" r="12" fill="#ef4444" />
          <text x="130" y="38" fontFamily="Arial, sans-serif" fontWeight="bold" fontSize="18" fill="#faf8f2" textAnchor="middle">!</text>
        </g>
      )}

      {(activity === 'flushing' || activity === 'tool_calling') && (
        <g>
          <line x1="28" y1="78" x2="38" y2="78" stroke="#7e9c8e" strokeWidth="2.2" strokeLinecap="round" className="log-line-1" />
          <line x1="42" y1="70" x2="54" y2="70" stroke="#7e9c8e" strokeWidth="2.2" strokeLinecap="round" className="log-line-2" />
        </g>
      )}
    </svg>
  );
}
