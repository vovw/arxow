"use client";

import { useEffect, useState, useCallback } from "react";

export function useVimMode() {
  const [vimMode, setVimMode] = useState(true);
  const [showHelp, setShowHelp] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("arxow-vim-mode");
    if (saved !== null) {
      setVimMode(saved === "true");
    }
  }, []);

  const toggleVimMode = useCallback(() => {
    const newValue = !vimMode;
    setVimMode(newValue);
    localStorage.setItem("arxow-vim-mode", String(newValue));
  }, [vimMode]);

  return {
    vimMode,
    toggleVimMode,
    showHelp,
    setShowHelp,
  };
}

export function useKeyboardShortcuts({
  onFirstPass,
  onSecondPass,
  onThirdPass,
  onToggleHelp,
  onToggleTheme,
  onExport,
  vimMode = true,
}) {
  useEffect(() => {
    if (!vimMode) return;

    const handleKeyPress = (e) => {
      // Don't trigger shortcuts if user is typing in an input
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") {
        return;
      }

      switch (e.key) {
        case "1":
          e.preventDefault();
          onFirstPass?.();
          break;
        case "2":
          e.preventDefault();
          onSecondPass?.();
          break;
        case "3":
          e.preventDefault();
          onThirdPass?.();
          break;
        case "?":
          e.preventDefault();
          onToggleHelp?.();
          break;
        case "d":
          if (e.shiftKey) {
            e.preventDefault();
            onToggleTheme?.();
          }
          break;
        case "e":
          e.preventDefault();
          onExport?.();
          break;
        case "j":
          e.preventDefault();
          window.scrollBy(0, 100);
          break;
        case "k":
          e.preventDefault();
          window.scrollBy(0, -100);
          break;
        case "g":
          if (e.shiftKey) {
            e.preventDefault();
            window.scrollTo(0, document.body.scrollHeight);
          } else {
            e.preventDefault();
            window.scrollTo(0, 0);
          }
          break;
        default:
          break;
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [
    vimMode,
    onFirstPass,
    onSecondPass,
    onThirdPass,
    onToggleHelp,
    onToggleTheme,
    onExport,
  ]);
}
