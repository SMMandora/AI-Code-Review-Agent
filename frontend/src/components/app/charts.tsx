"use client";

import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { CostPoint } from "@/lib/types";
import { formatUsd } from "@/lib/format";

const CHART_PALETTE = ["#3b82f6", "#8b5cf6", "#22c55e", "#f97316", "#eab308"];

const AXIS_COLOR = "#8a93a6";
const GRID_COLOR = "#1e2533";
const TOOLTIP_STYLE = { backgroundColor: "#121826", border: "1px solid #1e2533", borderRadius: "0.5rem", color: "#e6eaf2" };

// ----- Area Chart -----

export function CostAreaChart({ data }: { data: CostPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={288}>
      <AreaChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 8 }}>
        <defs>
          <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.35} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fill: AXIS_COLOR, fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: string) => v.slice(5)} // MM-DD
        />
        <YAxis
          tick={{ fill: AXIS_COLOR, fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => formatUsd(v, 2)}
          width={56}
        />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(value) => [formatUsd(Number(value ?? 0), 4), "Cost"]}
          labelStyle={{ color: AXIS_COLOR, marginBottom: 4 }}
          cursor={{ stroke: "#3b82f6", strokeWidth: 1, strokeDasharray: "4 2" }}
        />
        <Area
          type="monotone"
          dataKey="costUsd"
          stroke="#3b82f6"
          strokeWidth={2}
          fill="url(#costGrad)"
          dot={false}
          activeDot={{ r: 4, fill: "#3b82f6" }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

// ----- Bar Chart -----

export function CostBarChart({ data }: { data: { repo: string; costUsd: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={288}>
      <BarChart data={data} margin={{ top: 4, right: 8, bottom: 32, left: 8 }}>
        <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3" horizontal vertical={false} />
        <XAxis
          dataKey="repo"
          tick={{ fill: AXIS_COLOR, fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          angle={-30}
          textAnchor="end"
          interval={0}
        />
        <YAxis
          tick={{ fill: AXIS_COLOR, fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => formatUsd(v, 2)}
          width={56}
        />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(value) => [formatUsd(Number(value ?? 0), 4), "Cost"]}
          labelStyle={{ color: AXIS_COLOR, marginBottom: 4 }}
          cursor={{ fill: "rgba(59,130,246,0.08)" }}
        />
        <Bar dataKey="costUsd" fill="#3b82f6" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

// ----- Donut Chart -----

export function CostDonut({ data }: { data: { model: string; costUsd: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={288}>
      <PieChart>
        <Pie
          data={data}
          dataKey="costUsd"
          nameKey="model"
          cx="50%"
          cy="45%"
          innerRadius={64}
          outerRadius={100}
          paddingAngle={2}
        >
          {data.map((_entry, index) => (
            <Cell key={index} fill={CHART_PALETTE[index % CHART_PALETTE.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(value) => [formatUsd(Number(value ?? 0), 4), "Cost"]}
          labelStyle={{ color: AXIS_COLOR, marginBottom: 4 }}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: 11, color: AXIS_COLOR }}
          formatter={(value: string) => (
            <span style={{ color: "#e6eaf2" }}>{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
