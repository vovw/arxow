"use client";

import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
} from "@/components/ui/alert-dialog";
import { Card, CardContent } from "@/components/ui/card";

export function KeyboardHelp({ open, onClose }) {
  const shortcuts = [
    { key: "1", description: "Run First Pass analysis" },
    { key: "2", description: "Run Second Pass analysis" },
    { key: "3", description: "Run Third Pass analysis" },
    { key: "j", description: "Scroll down" },
    { key: "k", description: "Scroll up" },
    { key: "g", description: "Go to top" },
    { key: "G", description: "Go to bottom" },
    { key: "D", description: "Toggle dark mode" },
    { key: "e", description: "Export analysis" },
    { key: "?", description: "Show this help" },
    { key: "ESC", description: "Close modals" },
  ];

  return (
    <AlertDialog open={open} onOpenChange={onClose}>
      <AlertDialogContent className="max-w-2xl">
        <AlertDialogHeader>
          <AlertDialogTitle className="text-2xl">
            ⌨️ Keyboard Shortcuts
          </AlertDialogTitle>
          <AlertDialogDescription>
            Vim-style keybindings for efficient navigation
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div className="grid grid-cols-2 gap-3 mt-4">
          {shortcuts.map((shortcut) => (
            <Card key={shortcut.key} className="border-muted">
              <CardContent className="p-3 flex items-center gap-3">
                <kbd className="px-3 py-1.5 text-sm font-semibold text-foreground bg-muted border border-border rounded-lg shadow-sm min-w-[3rem] text-center">
                  {shortcut.key}
                </kbd>
                <span className="text-sm text-muted-foreground">
                  {shortcut.description}
                </span>
              </CardContent>
            </Card>
          ))}
        </div>
        <p className="text-xs text-muted-foreground mt-4">
          Press ESC or click outside to close this dialog
        </p>
      </AlertDialogContent>
    </AlertDialog>
  );
}
