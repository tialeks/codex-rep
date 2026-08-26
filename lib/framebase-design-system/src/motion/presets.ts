export const motionTokens = {
  instant: 0.12,
  fast: 0.2,
  base: 0.32,
  slow: 0.48,
  easeOut: [0.16, 1, 0.3, 1] as const,
  easeStandard: [0.22, 1, 0.36, 1] as const,
  spring: { type: "spring", stiffness: 360, damping: 30 } as const,
  springSoft: { type: "spring", stiffness: 220, damping: 25 } as const,
  springSnappy: { type: "spring", stiffness: 520, damping: 34 } as const
};

export const pressMotion = { scale: 0.97 } as const;
export const hoverLiftMotion = { y: -2 } as const;
