"use client";

import React, { useEffect, useRef, useState, useMemo } from "react";
import * as d3 from "d3";
import { Search, Filter, Sparkles, Layers } from "lucide-react";
import type { GraphNode, GraphEdge } from "@/lib/api";

export const ENTITY_COLORS: Record<string, { bg: string; glow: string; text: string; border: string }> = {
  CONCEPT: { bg: "#10b981", glow: "rgba(16, 185, 129, 0.4)", text: "#ecfdf5", border: "#059669" },
  PERSON: { bg: "#0ea5e9", glow: "rgba(14, 165, 233, 0.4)", text: "#f0f9ff", border: "#0284c7" },
  LOCATION: { bg: "#f59e0b", glow: "rgba(245, 158, 11, 0.4)", text: "#fffbeb", border: "#d97706" },
  WORK: { bg: "#a855f7", glow: "rgba(168, 85, 247, 0.4)", text: "#faf5ff", border: "#9333ea" },
  PHILOSOPHY: { bg: "#f43f5e", glow: "rgba(244, 63, 94, 0.4)", text: "#fff1f2", border: "#e11d48" },
  THEME: { bg: "#6366f1", glow: "rgba(99, 102, 241, 0.4)", text: "#eef2ff", border: "#4f46e5" },
  ORGANIZATION: { bg: "#06b6d4", glow: "rgba(6, 182, 212, 0.4)", text: "#ecfeff", border: "#0891b2" },
  EVENT: { bg: "#ec4899", glow: "rgba(236, 72, 153, 0.4)", text: "#fdf2f8", border: "#db2777" },
};

const DEFAULT_COLOR = {
  bg: "#64748b",
  glow: "rgba(100, 116, 139, 0.4)",
  text: "#f8fafc",
  border: "#475569",
};

export interface GraphCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string | null) => void;
  height?: number;
}

interface SimulationNode extends GraphNode, d3.SimulationNodeDatum {}
interface SimulationLink extends d3.SimulationLinkDatum<SimulationNode> {
  id: string;
  relation: string;
  label: string;
  weight: number;
}

export const GraphCanvas: React.FC<GraphCanvasProps> = ({
  nodes,
  edges,
  selectedNodeId,
  onSelectNode,
  height = 600,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set());
  const [hoveredNode, setHoveredNode] = useState<SimulationNode | null>(null);

  // Available entity types in current graph
  const availableTypes = useMemo(() => {
    const types = new Set<string>();
    nodes.forEach((n) => types.add((n.type || n.entity_type || "CONCEPT").toUpperCase()));
    return Array.from(types);
  }, [nodes]);

  // Filter nodes and links based on search and type filters
  const filteredData = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    const activeNodes = nodes.filter((n) => {
      const typeKey = (n.type || n.entity_type || "CONCEPT").toUpperCase();
      const matchesType = selectedTypes.size === 0 || selectedTypes.has(typeKey);
      const matchesSearch =
        !query ||
        n.name.toLowerCase().includes(query) ||
        (n.original_name && n.original_name.toLowerCase().includes(query)) ||
        (n.description && n.description.toLowerCase().includes(query));
      return matchesType && matchesSearch;
    });

    const activeNodeIds = new Set(activeNodes.map((n) => n.id || n.node_id));
    const activeEdges = edges.filter((e) => {
      const srcId = typeof e.source === "object" ? (e.source as any).id || (e.source as any).node_id : e.source || e.source_node_id;
      const tgtId = typeof e.target === "object" ? (e.target as any).id || (e.target as any).node_id : e.target || e.target_node_id;
      return activeNodeIds.has(srcId) && activeNodeIds.has(tgtId);
    });

    return { activeNodes, activeEdges };
  }, [nodes, edges, searchQuery, selectedTypes]);

  const toggleTypeFilter = (type: string) => {
    setSelectedTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  };

  // D3 force simulation setup
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const canvasHeight = canvas.height;

    // Deep copy nodes and links for simulation
    const simNodes: SimulationNode[] = filteredData.activeNodes.map((d) => ({
      ...d,
      id: d.id || d.node_id,
    }));
    const nodeMap = new Map(simNodes.map((d) => [d.id, d]));

    const simLinks: SimulationLink[] = filteredData.activeEdges
      .map((e) => {
        const srcId = typeof e.source === "object" ? (e.source as any).id || (e.source as any).node_id : e.source || e.source_node_id;
        const tgtId = typeof e.target === "object" ? (e.target as any).id || (e.target as any).node_id : e.target || e.target_node_id;
        return {
          id: e.id || e.edge_id,
          source: nodeMap.get(srcId) as SimulationNode,
          target: nodeMap.get(tgtId) as SimulationNode,
          relation: e.relation || e.relation_type,
          label: e.label || (e.relation_type || "RELATED_TO").replace("_", " ").toLowerCase(),
          weight: e.weight || 1.0,
        };
      })
      .filter((l) => l.source && l.target);

    // D3 Simulation with compact, well-proportioned forces
    const simulation = d3
      .forceSimulation<SimulationNode>(simNodes)
      .force(
        "link",
        d3
          .forceLink<SimulationNode, SimulationLink>(simLinks)
          .id((d) => d.id)
          .distance(75)
          .strength(0.7)
      )
      .force("charge", d3.forceManyBody().strength(-140).distanceMax(350))
      .force("center", d3.forceCenter(width / 2, canvasHeight / 2).strength(0.1))
      .force("collision", d3.forceCollide().radius((d: any) => Math.max(10, Math.min(20, 7 + (d.frequency || 1) * 1.5))))
      .alphaDecay(0.025);

    // Zoom transform state
    let transform = d3.zoomIdentity;

    const render = () => {
      ctx.save();
      ctx.clearRect(0, 0, width, canvasHeight);

      // Background gradient
      const bgGrad = ctx.createRadialGradient(width / 2, canvasHeight / 2, 50, width / 2, canvasHeight / 2, width);
      bgGrad.addColorStop(0, "#09090b");
      bgGrad.addColorStop(1, "#030303");
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, width, canvasHeight);

      // Subtle grid
      ctx.save();
      ctx.translate(transform.x, transform.y);
      ctx.scale(transform.k, transform.k);

      ctx.strokeStyle = "rgba(255, 255, 255, 0.03)";
      ctx.lineWidth = 1 / transform.k;
      const gridSize = 40;
      const startX = Math.floor(-width / transform.k / gridSize) * gridSize;
      const endX = Math.ceil((width * 2) / transform.k / gridSize) * gridSize;
      const startY = Math.floor(-canvasHeight / transform.k / gridSize) * gridSize;
      const endY = Math.ceil((canvasHeight * 2) / transform.k / gridSize) * gridSize;

      for (let x = startX; x <= endX; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, startY);
        ctx.lineTo(x, endY);
        ctx.stroke();
      }
      for (let y = startY; y <= endY; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(startX, y);
        ctx.lineTo(endX, y);
        ctx.stroke();
      }

      // 1. Draw Links
      simLinks.forEach((link) => {
        const s = link.source as SimulationNode;
        const t = link.target as SimulationNode;
        if (s.x === undefined || s.y === undefined || t.x === undefined || t.y === undefined) return;

        const isSelectedLink =
          selectedNodeId && (s.id === selectedNodeId || t.id === selectedNodeId);

        ctx.beginPath();
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(t.x, t.y);

        if (isSelectedLink) {
          ctx.strokeStyle = "rgba(52, 211, 153, 0.85)";
          ctx.lineWidth = 2.0;
        } else {
          ctx.strokeStyle = "rgba(113, 113, 122, 0.35)";
          ctx.lineWidth = Math.max(0.8, (link.weight || 1) * 1.1);
        }
        ctx.stroke();

        // Edge label (drawn when zoomed in or link selected)
        if (transform.k > 0.8 || isSelectedLink) {
          const midX = (s.x + t.x) / 2;
          const midY = (s.y + t.y) / 2;

          ctx.font = "9px Inter, system-ui, sans-serif";
          ctx.fillStyle = isSelectedLink ? "#34d399" : "rgba(161, 161, 170, 0.75)";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";

          ctx.save();
          ctx.translate(midX, midY);
          ctx.fillText(link.label, 0, -3);
          ctx.restore();
        }
      });

      // 2. Draw Nodes (Compact, elegant Obsidian-style nodes)
      simNodes.forEach((node) => {
        if (node.x === undefined || node.y === undefined) return;

        const isSelected = selectedNodeId === node.id;
        const isHovered = hoveredNode?.id === node.id;
        const typeKey = (node.type || node.entity_type || "CONCEPT").toUpperCase();
        const color = ENTITY_COLORS[typeKey] || DEFAULT_COLOR;

        // Small, sleek node radius (5px to 9px base)
        const baseRadius = Math.max(5, Math.min(9, 4 + (node.frequency || 1) * 0.9));
        const radius = isSelected ? baseRadius * 1.4 : isHovered ? baseRadius * 1.25 : baseRadius;

        // Outer glow
        if (isSelected || isHovered) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, radius + 6, 0, 2 * Math.PI);
          ctx.fillStyle = color.glow;
          ctx.fill();
        }

        // Main circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = isSelected ? "#ffffff" : color.bg;
        ctx.fill();

        // Border
        ctx.strokeStyle = isSelected ? color.bg : color.border;
        ctx.lineWidth = isSelected ? 2.5 : 1.5;
        ctx.stroke();

        // Node Title Label
        ctx.font = `${isSelected ? "600 11px" : "10px"} Inter, system-ui, sans-serif`;
        ctx.fillStyle = isSelected ? "#ffffff" : "#f4f4f5";
        ctx.textAlign = "center";
        ctx.textBaseline = "top";

        const displayName = node.original_name ? `${node.name} (${node.original_name})` : node.name;
        ctx.fillText(displayName, node.x, node.y + radius + 4);
      });

      ctx.restore();
      ctx.restore();
    };

    simulation.on("tick", render);

    // Zoom behavior
    const zoomBehavior = d3
      .zoom<HTMLCanvasElement, unknown>()
      .scaleExtent([0.2, 4])
      .on("zoom", (event) => {
        transform = event.transform;
        render();
      });

    const d3Canvas = d3.select(canvas);
    d3Canvas.call(zoomBehavior as any);

    // Drag behavior
    let isDragging = false;
    let dragNode: SimulationNode | null = null;

    const findNodeAt = (screenX: number, screenY: number): SimulationNode | null => {
      const rect = canvas.getBoundingClientRect();
      const mouseX = screenX - rect.left;
      const mouseY = screenY - rect.top;

      const simX = (mouseX - transform.x) / transform.k;
      const simY = (mouseY - transform.y) / transform.k;

      for (const node of simNodes) {
        if (node.x === undefined || node.y === undefined) continue;
        const hitRadius = Math.max(10, Math.min(16, 6 + (node.frequency || 1) * 1.5));
        const dist = Math.hypot(node.x - simX, node.y - simY);
        if (dist <= hitRadius) {
          return node;
        }
      }
      return null;
    };

    const onMouseDown = (e: MouseEvent) => {
      const node = findNodeAt(e.clientX, e.clientY);
      if (node) {
        isDragging = true;
        dragNode = node;
        node.fx = node.x;
        node.fy = node.y;
        simulation.alphaTarget(0.3).restart();
      }
    };

    const onMouseMove = (e: MouseEvent) => {
      if (isDragging && dragNode) {
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        dragNode.fx = (mouseX - transform.x) / transform.k;
        dragNode.fy = (mouseY - transform.y) / transform.k;
      } else {
        const node = findNodeAt(e.clientX, e.clientY);
        setHoveredNode(node);
        canvas.style.cursor = node ? "pointer" : "grab";
      }
    };

    const onMouseUp = () => {
      if (isDragging && dragNode) {
        dragNode.fx = null;
        dragNode.fy = null;
        simulation.alphaTarget(0);
        isDragging = false;
        dragNode = null;
      }
    };

    const onClick = (e: MouseEvent) => {
      const node = findNodeAt(e.clientX, e.clientY);
      if (node) {
        onSelectNode(node.id || node.node_id);
      } else {
        onSelectNode(null);
      }
    };

    canvas.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    canvas.addEventListener("click", onClick);

    return () => {
      simulation.stop();
      canvas.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      canvas.removeEventListener("click", onClick);
    };
  }, [filteredData, selectedNodeId, onSelectNode, height]);

  // Handle Resize
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current && canvasRef.current) {
        canvasRef.current.width = containerRef.current.clientWidth;
        canvasRef.current.height = height;
      }
    };

    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [height]);

  return (
    <div ref={containerRef} className="relative w-full rounded-2xl overflow-hidden border border-zinc-800 bg-zinc-950 shadow-2xl">
      {/* Top Overlay Controls Bar */}
      <div className="absolute top-4 left-4 right-4 z-10 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
        {/* Search Input */}
        <div className="flex items-center gap-2 bg-zinc-900/90 backdrop-blur-md border border-zinc-800 px-3 py-1.5 rounded-xl shadow-lg pointer-events-auto">
          <Search className="w-4 h-4 text-zinc-400" />
          <input
            type="text"
            placeholder="Search concepts or entities..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-transparent text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none w-44 sm:w-56"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery("")} className="text-zinc-500 hover:text-zinc-300 text-xs">
              ✕
            </button>
          )}
        </div>

        {/* Entity Type Filter Badges */}
        <div className="flex flex-wrap items-center gap-1.5 pointer-events-auto">
          {availableTypes.map((type) => {
            const color = ENTITY_COLORS[type] || DEFAULT_COLOR;
            const isSelected = selectedTypes.size === 0 || selectedTypes.has(type);

            return (
              <button
                key={type}
                onClick={() => toggleTypeFilter(type)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all flex items-center gap-1.5 border shadow-sm ${
                  isSelected
                    ? "bg-zinc-900/90 text-zinc-200 border-zinc-700"
                    : "bg-zinc-950/60 text-zinc-600 border-zinc-900 opacity-60"
                }`}
              >
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color.bg }} />
                <span>{type}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Canvas */}
      <canvas ref={canvasRef} className="w-full block" style={{ height: `${height}px` }} />

      {/* Bottom Status Info */}
      <div className="absolute bottom-3 left-4 right-4 flex items-center justify-between text-[11px] text-zinc-500 pointer-events-none">
        <div className="flex items-center gap-2 bg-zinc-900/80 backdrop-blur-md px-2.5 py-1 rounded-lg border border-zinc-800/80">
          <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
          <span>
            {filteredData.activeNodes.length} nodes · {filteredData.activeEdges.length} connections
          </span>
        </div>
        <div className="bg-zinc-900/80 backdrop-blur-md px-2.5 py-1 rounded-lg border border-zinc-800/80">
          Click node to inspect · Drag to reposition · Scroll to zoom
        </div>
      </div>
    </div>
  );
};
