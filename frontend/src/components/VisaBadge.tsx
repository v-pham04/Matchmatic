import type { VisaSignal } from "../types";
 
interface Props {
  signal: VisaSignal;
  size?: "sm" | "md";
}
 
const config = {
  open:         { bg: "bg-green-100",  text: "text-green-800",  label: "✓ Visa Friendly"    },
  citizen_only: { bg: "bg-red-100",    text: "text-red-800",    label: "✗ Citizens Only"     },
  unclear:      { bg: "bg-yellow-100", text: "text-yellow-800", label: "? Visa Unclear"      },
};
 
export default function VisaBadge({ signal, size = "sm" }: Props) {
  if (!signal) return null;
 
  const c = config[signal] ?? config.unclear;
 
  return (
    <span className={`inline-flex items-center rounded-full font-medium ${ 
      size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm"
    } ${c.bg} ${c.text}`}>
      {c.label}
    </span>
  );
}
