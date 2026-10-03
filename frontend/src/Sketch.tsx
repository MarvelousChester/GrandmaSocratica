// Small hand-drawn building blocks shared by the UI.

/** Defines the wobble filter that `.sketch` backgrounds point at. Render once. */
export function SketchDefs() {
  return (
    <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden="true" focusable="false">
      <defs>
        <filter id="rough-ui">
          <feTurbulence type="fractalNoise" baseFrequency="0.025" numOctaves="2" seed="5" />
          <feDisplacementMap in="SourceGraphic" scale="5" />
        </filter>
      </defs>
    </svg>
  )
}

/** A divider line with a slight hand-drawn sag. */
export function Rule() {
  return (
    <svg className="rule" viewBox="0 0 500 8" preserveAspectRatio="none" aria-hidden="true">
      <path d="M0 4 Q 120 1.5 250 4 T 500 4" fill="none" stroke="currentColor" strokeWidth="3" vectorEffect="non-scaling-stroke" strokeLinecap="round" />
    </svg>
  )
}

export function PencilIcon() {
  return (
    <svg viewBox="0 0 40 40" aria-hidden="true">
      <g fill="#fff" stroke="currentColor" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round">
        <path d="M5 35 L9 22 L27 4 L36 13 L18 31 Z" />
        <path d="M9 22 L18 31" fill="none" />
        <path d="M23 8 L32 17" fill="none" />
      </g>
    </svg>
  )
}

export function PlusIcon() {
  return (
    <svg viewBox="0 0 40 40" aria-hidden="true">
      <path d="M20 8 V32 M8 20 H32" stroke="currentColor" strokeWidth="5" strokeLinecap="round" fill="none" />
    </svg>
  )
}

export function TrashIcon() {
  return (
    <svg viewBox="0 0 40 40" aria-hidden="true">
      <g fill="#fff" stroke="currentColor" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round">
        <path d="M9 11 L11.5 35 H28.5 L31 11 Z" />
        <path d="M5 11 H35" fill="none" />
        <path d="M15 11 V7 H25 V11" fill="none" />
        <path d="M16 17 V29 M24 17 V29" fill="none" />
      </g>
    </svg>
  )
}
