import React, { useState } from "react";
import { motion } from "framer-motion";

type Props = { summary?: string };

export default function AISummaryChat({ summary }: Props) {
  const [expanded, setExpanded] = useState(true);

  return (
    <motion.div
      className="ai-chat"
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
    >
      <div className="chat-header" onClick={() => setExpanded(!expanded)}>
        <h3>💬 AI Summary & Insights</h3>
        <span>{expanded ? "▼" : "▲"}</span>
      </div>
      {expanded && (
        <motion.div
          className="chat-body"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4 }}
        >
          {summary ? (
            <div className="chat-bubble ai">{summary}</div>
          ) : (
            <div className="chat-placeholder">
              AI summary will appear here after comparison
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}
