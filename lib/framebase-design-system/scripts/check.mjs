import { access, readFile, readdir } from "node:fs/promises";
import { resolve } from "node:path";
const root = resolve(import.meta.dirname, "..");
const manifest = JSON.parse(await readFile(resolve(root,"assets/service-logos/manifest.json"),"utf8"));
if (manifest.length !== 50) throw new Error(`Ожидалось 50 логотипов, найдено ${manifest.length}`);
const marks = (await readdir(resolve(root,"assets/service-logos/loader-marks"))).filter(x=>x.endsWith(".svg"));
if (marks.length !== 50) throw new Error(`Ожидалось 50 loader marks, найдено ${marks.length}`);
for (const path of ["src/vendor/morphicons/react/index.tsx","src/vendor/thinking-logos/ThinkingLogo.tsx","licenses/MORPHICONS-MIT.txt","licenses/THINKING-LOGOS-MIT.txt"]) await access(resolve(root,path));
console.log("✓ 50 логотипов, 50 loader marks, обе локальные библиотеки и лицензии на месте");
