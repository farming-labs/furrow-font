"use client";

import { useEffect, useRef, useState } from "react";

export function CopyButton({
  text,
  label = "Copy",
  className = "copy-btn",
}: {
  text: string;
  label?: string;
  className?: string;
}) {
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");
  const timer = useRef<number | undefined>(undefined);

  useEffect(() => () => window.clearTimeout(timer.current), []);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setState("copied");
    } catch {
      setState("failed");
    }
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setState("idle"), 1600);
  }

  return (
    <button
      type="button"
      className={className}
      data-copied={state === "copied"}
      onClick={copy}
      aria-label={`${label} to clipboard`}
    >
      {state === "copied" ? "Copied" : state === "failed" ? "Failed" : "Copy"}
      <span className="sr-only" aria-live="polite">
        {state === "copied" ? "Copied to clipboard" : state === "failed" ? "Copy failed" : ""}
      </span>
    </button>
  );
}
