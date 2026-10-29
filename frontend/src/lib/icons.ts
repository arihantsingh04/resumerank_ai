import {
  Apple,
  Atom,
  BarChart3,
  BrainCircuit,
  Briefcase,
  Bug,
  Cloud,
  Cpu,
  Infinity as InfinityIcon,
  Layers,
  LayoutTemplate,
  Server,
  ShieldCheck,
  Smartphone,
  TabletSmartphone,
  type LucideIcon,
} from "lucide-react";

// Template icons are named by the backend (app/data/templates.py) using lucide names.
const ICONS: Record<string, LucideIcon> = {
  server: Server,
  "layout-template": LayoutTemplate,
  layers: Layers,
  smartphone: Smartphone,
  apple: Apple,
  "tablet-smartphone": TabletSmartphone,
  atom: Atom,
  infinity: InfinityIcon,
  cloud: Cloud,
  "bar-chart-3": BarChart3,
  "brain-circuit": BrainCircuit,
  bug: Bug,
  "shield-check": ShieldCheck,
  cpu: Cpu,
};

export const iconFor = (name: string): LucideIcon => ICONS[name] ?? Briefcase;
