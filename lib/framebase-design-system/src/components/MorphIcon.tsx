import type { ComponentProps } from "react";
import { MorphIcon as LocalMorphIcon } from "../vendor/morphicons/react/index";

export type MorphingIconProps = Omit<ComponentProps<typeof LocalMorphIcon>, "reducedMotion">;
export function MorphingIcon(props: MorphingIconProps) { return <LocalMorphIcon reducedMotion="user" {...props}/>; }

export const morphIconShapes = {
  menu: "M4 6h16M4 12h16M4 18h16",
  close: "M6 6l12 12M18 6L6 18",
  play: "M8 5l11 7-11 7z",
  pause: "M9 5v14M15 5v14",
  plus: "M12 5v14M5 12h14",
  check: "M5 12l4 4L19 6",
  arrowRight: "M5 12h14M13 6l6 6-6 6",
  arrowLeft: "M19 12H5M11 6l-6 6 6 6",
  search: "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14M16 16l4 4"
} as const;
