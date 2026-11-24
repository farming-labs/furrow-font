"use client";

import { useSyncExternalStore } from "react";

export type Face = "sans" | "mono";

/**
 * The family the whole page is showing, switched from the header. It lives on
 * `<html data-face>` so CSS can follow it without a render, and components read
 * it through `useFace`.
 */
const listeners = new Set<() => void>();

function read(): Face {
  return document.documentElement.dataset.face === "mono" ? "mono" : "sans";
}

export function setFace(face: Face) {
  document.documentElement.dataset.face = face;
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function useFace(): Face {
  return useSyncExternalStore(subscribe, read, () => "sans");
}

export const FACE_FONT: Record<Face, string> = {
  sans: "var(--sans)",
  mono: "var(--mono)",
};
