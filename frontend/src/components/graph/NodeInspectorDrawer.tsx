"use client";

import React, { useEffect, useState } from "react";
import {
  X,
  ArrowRight,
  ArrowLeft,
  Languages,
  Sparkles,
  ChevronRight,
  Loader2,
  AlertCircle,
  Network,
  ListChecks,
  FileText,
} from "lucide-react";
import { getNodeDetails, type NodeDetailsResponse } from "@/lib/api";
import { ENTITY_COLORS } from "./GraphCanvas";

export interface NodeInspectorDrawerProps {
  nodeId: string | null;
  onClose: () => void;
  onSelectNode: (nodeId: string) => void;
}

export const NodeInspectorDrawer: React.FC<NodeInspectorDrawerProps> = ({
  nodeId,
  onClose,
  onSelectNode,
}) => {
  const [loading, setLoading] = useState(false);
  const [details, setDetails] = useState<NodeDetailsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!nodeId) {
      setDetails(null);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);

    getNodeDetails(nodeId)
      .then((data) => {
        if (isMounted) {
          setDetails(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || "Failed to load node details");
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [nodeId]);

  if (!nodeId) return null;

  const typeKey = (details?.node.entity_type || details?.node.type || "CONCEPT").toUpperCase();
  const color = ENTITY_COLORS[typeKey] || { bg: "#64748b", glow: "rgba(100,116,139,0.4)", text: "#f8fafc", border: "#475569" };

  const summaryText =
    details?.summary ||
    details?.node.summary ||
    details?.node.description ||
    `${details?.node.name} is a key ${(details?.node.entity_type || "concept").toLowerCase()} identified in this document.`;

  const keyInsights =
    details?.key_insights ||
    details?.node.key_insights ||
    [];

  return (
    <aside
      className="fixed inset-y-0 right-0 w-full sm:w-[460px] lg:w-[490px] bg-zinc-950/98 backdrop-blur-2xl border-l border-zinc-800 shadow-2xl z-50 flex flex-col transform transition-transform duration-300 ease-out"
      aria-label="Node Inspector"
    >
      {/* 1. TOP SECTION: SELECTED NODE HEADER */}
      <div className="p-5 sm:p-6 border-b border-zinc-800 flex items-start justify-between gap-4 bg-zinc-900/50">
        <div className="space-y-1.5 flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className="px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border shadow-sm"
              style={{
                backgroundColor: `${color.bg}22`,
                borderColor: color.border,
                color: color.bg,
              }}
            >
              {details?.node.entity_type || details?.node.type || "CONCEPT"}
            </span>

            {details?.node.frequency && details.node.frequency > 1 && (
              <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-zinc-800 text-zinc-300 border border-zinc-700">
                {details.node.frequency} references
              </span>
            )}

            {details?.node.document_name && (
              <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-zinc-900 text-zinc-400 border border-zinc-800 truncate max-w-[160px]" title={details.node.document_name}>
                {details.node.document_name}
              </span>
            )}
          </div>

          <h2 className="text-xl font-bold text-zinc-100 tracking-tight break-words">
            {details?.node.name || "Loading concept..."}
          </h2>

          {details?.node.original_name && (
            <p className="text-sm font-medium text-amber-400 flex items-center gap-1.5">
              <Languages className="w-3.5 h-3.5 text-amber-500 shrink-0" />
              <span>{details.node.original_name}</span>
            </p>
          )}
        </div>

        <button
          onClick={onClose}
          className="p-1.5 rounded-lg bg-zinc-900 text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors border border-zinc-800 shrink-0"
          title="Close Inspector"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Content Body */}
      <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-6">
        {loading && (
          <div className="flex flex-col items-center justify-center h-48 text-zinc-400 gap-3">
            <Loader2 className="w-7 h-7 text-emerald-500 animate-spin" />
            <p className="text-xs font-medium text-zinc-400">Summarizing concept knowledge & relationships...</p>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-red-950/40 border border-red-900/50 text-red-400 text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {details && !loading && (
          <>
            {/* 1. NODE-SPECIFIC SUMMARY (CONCISE EXPLANATION) */}
            <div className="space-y-2">
              <div className="p-4 rounded-xl bg-zinc-900/70 border border-zinc-800/90 space-y-2.5">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                  Node Summary
                </h3>
                <p className="text-xs sm:text-sm text-zinc-200 leading-relaxed">
                  {summaryText}
                </p>
              </div>
            </div>

            {/* 2. KEY CONTEXTUAL TAKEAWAYS */}
            {keyInsights.length > 0 && (
              <div className="space-y-2.5 pt-2 border-t border-zinc-800/60">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                  <ListChecks className="w-3.5 h-3.5 text-emerald-400" />
                  Key Insights & Context
                </h3>
                <div className="space-y-2">
                  {keyInsights.map((insight, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-zinc-900/50 border border-zinc-800/70 flex items-start gap-2.5"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0 mt-1.5" />
                      <p className="text-xs text-zinc-300 leading-relaxed">
                        {insight}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 3. CONNECTED RELATIONSHIPS */}
            <div className="space-y-3 pt-2 border-t border-zinc-800/60">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                <Network className="w-3.5 h-3.5 text-zinc-400" />
                Connected Concepts ({details.connected_relations.length})
              </h3>

              {details.connected_relations.length === 0 ? (
                <p className="text-xs text-zinc-500 italic p-3 rounded-lg bg-zinc-900/30 border border-zinc-900">
                  No direct connections recorded for this node in the knowledge graph.
                </p>
              ) : (
                <div className="space-y-2">
                  {details.connected_relations.map((rel) => {
                    const isOutgoing = rel.direction === "outgoing";
                    const otherNodeId = isOutgoing ? rel.target_node_id : rel.source_node_id;
                    const otherNodeName = isOutgoing ? rel.target_node_name : rel.source_node_name;
                    const otherNodeType = (isOutgoing ? rel.target_node_type : rel.source_node_type) || "CONCEPT";
                    const otherColor = ENTITY_COLORS[otherNodeType.toUpperCase()] || { bg: "#64748b" };

                    return (
                      <div
                        key={rel.edge_id}
                        className="p-3 rounded-xl bg-zinc-900/50 border border-zinc-800/80 hover:border-zinc-700 transition-all flex items-start justify-between gap-3 group"
                      >
                        <div className="space-y-1 flex-1 min-w-0">
                          <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-400">
                            {isOutgoing ? (
                              <ArrowRight className="w-3.5 h-3.5 text-emerald-500" />
                            ) : (
                              <ArrowLeft className="w-3.5 h-3.5 text-blue-400" />
                            )}
                            <span className="uppercase tracking-wider text-[11px] font-semibold">
                              {rel.relation_type.replace(/_/g, " ")}
                            </span>
                          </div>

                          <div className="flex items-center gap-2">
                            <span
                              className="w-2 h-2 rounded-full shrink-0"
                              style={{ backgroundColor: otherColor.bg }}
                            />
                            <p className="text-sm font-medium text-zinc-200 truncate">
                              {otherNodeName}
                            </p>
                            <span className="text-[10px] text-zinc-500 font-mono">
                              ({otherNodeType})
                            </span>
                          </div>

                          {rel.description && (
                            <p className="text-xs text-zinc-400 line-clamp-2">
                              {rel.description}
                            </p>
                          )}
                        </div>

                        {otherNodeId && (
                          <button
                            onClick={() => onSelectNode(otherNodeId)}
                            className="p-1.5 rounded-lg bg-zinc-800/50 text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors shrink-0 group-hover:border-zinc-600 border border-transparent"
                            title={`Inspect ${otherNodeName}`}
                          >
                            <ChevronRight className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </aside>
  );
};
