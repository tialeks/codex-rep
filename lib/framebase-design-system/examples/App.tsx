import { useState } from "react";
import { BrandProvider, BrandLogo, BrandThinkingLogo, LoadingButton, SegmentedControl, Surface, Toggle, morphIconShapes, MorphingIcon } from "../src";

const brand = { id:"01-nova", title:"Nova", logoSrc:"/brand-logo.svg", loaderSrc:"/brand-loader-mark.svg", tint:"#2867EB" };
export function App(){const [tab,setTab]=useState("flow");const [on,setOn]=useState(true);return <BrandProvider brand={brand}><main className="lf-root" style={{minHeight:"100vh",padding:32}}><Surface><div className="lf-row"><BrandLogo/><h1>Новый сервис</h1></div><SegmentedControl items={[{value:"flow",label:"Флоу"},{value:"kit",label:"Кит"}]} value={tab} onChange={setTab}/><div className="lf-row"><LoadingButton state="pending"/><BrandThinkingLogo state="generating" size={40}/><Toggle checked={on} onChange={setOn} label="Анимации"/><MorphingIcon icon={on?morphIconShapes.play:morphIconShapes.pause}/></div></Surface></main></BrandProvider>}
