import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ThinkingLogo, type ThinkingLogoProps } from "../vendor/thinking-logos/ThinkingLogo";

export type BrandConfig = { id: string; title: string; logoSrc: string; loaderSrc: string; tint: string };
export const defaultBrand: BrandConfig = { id: "01-nova", title: "Nova", logoSrc: "/brand-logo.svg", loaderSrc: "/brand-loader-mark.svg", tint: "#4f8cff" };
const BrandContext = createContext<BrandConfig>(defaultBrand);

export function BrandProvider({ brand = defaultBrand, children }: { brand?: BrandConfig; children: ReactNode }) {
  return <BrandContext.Provider value={brand}>{children}</BrandContext.Provider>;
}
export function useBrand() { return useContext(BrandContext); }

export function BrandLogo({ size = 40, className = "", alt }: { size?: number; className?: string; alt?: string }) {
  const brand = useBrand();
  return <img className={`lf-brand ${className}`} src={brand.logoSrc} width={size} height={size} alt={alt ?? brand.title} />;
}

export function BrandThinkingLogo({ size = 20, state = "working", className = "", ...props }: Omit<ThinkingLogoProps, "logo"> & { className?: string }) {
  const brand = useBrand();
  const reduced = useReducedMotion();
  const [svg, setSvg] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    fetch(brand.loaderSrc).then(r => { if (!r.ok) throw new Error(`Logo ${r.status}`); return r.text(); }).then(v => active && setSvg(v)).catch(() => active && setSvg(null));
    return () => { active = false; };
  }, [brand.loaderSrc]);
  return <span className={`lf-brand-loader ${className}`} style={{ width: size, height: size }}>
    <AnimatePresence mode="wait" initial={false}>
      {svg && !reduced ? <motion.span key="thinking" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}><ThinkingLogo logo={{ svg }} size={size} state={state} tint={brand.tint} {...props}/></motion.span> : <motion.img key="mark" src={brand.loaderSrc} alt="" width={size} height={size} animate={reduced ? undefined : { opacity: [0.45, 1, 0.45] }} transition={{ duration: 1.25, repeat: Infinity }}/>} 
    </AnimatePresence>
  </span>;
}
