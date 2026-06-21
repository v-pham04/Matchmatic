import type { MatchLevel } from "../types";
 
interface Props {
  score: number;
  level: MatchLevel;
  size?: "sm" | "md";
}
 
const config: Record<MatchLevel, { bg: string; text: string; dot: string }> = {
  HIGH:   { bg: "bg-green-100",  text: "text-green-800",  dot: "bg-green-500"  },
  MEDIUM: { bg: "bg-yellow-100", text: "text-yellow-800", dot: "bg-yellow-500" },
  LOW:    { bg: "bg-red-100",    text: "text-red-800",    dot: "bg-red-500"    },
};
 
export default function MatchBadge({ score, level, size = "md" }: Props) {
  const c = config[level] ?? config.LOW;
  const isSmall = size === "sm";
 
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full font-medium ${ 
      isSmall ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm"
    } ${c.bg} ${c.text}`}>
      <span className={`rounded-full ${isSmall ? "w-1.5 h-1.5" : "w-2 h-2"} ${c.dot}`} />
      {score}% {level}
    </span>
  );
}
