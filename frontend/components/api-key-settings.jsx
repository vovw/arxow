"use client";

import { useState, useEffect } from "react";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Key, Eye, EyeOff, AlertCircle } from "lucide-react";

export function ApiKeySettings({ open, onClose }) {
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    // Load saved API key
    const savedKey = localStorage.getItem("arxow-api-key");
    if (savedKey) {
      setApiKey(savedKey);
      setSaved(true);
    }
  }, [open]);

  const handleSave = () => {
    if (apiKey.trim()) {
      localStorage.setItem("arxow-api-key", apiKey.trim());
      setSaved(true);
      setTimeout(() => {
        onClose();
      }, 1000);
    }
  };

  const handleClear = () => {
    localStorage.removeItem("arxow-api-key");
    setApiKey("");
    setSaved(false);
  };

  return (
    <AlertDialog open={open} onOpenChange={onClose}>
      <AlertDialogContent className="max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            Bring Your Own API Key
          </AlertDialogTitle>
          <AlertDialogDescription>
            Use your own OpenRouter API key for unlimited usage
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="api-key">OpenRouter API Key</Label>
            <div className="relative">
              <Input
                id="api-key"
                type={showKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-or-v1-..."
                className="pr-10"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showKey ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
            <p className="text-xs text-muted-foreground">
              Get your API key from{" "}
              <a
                href="https://openrouter.ai/keys"
                target="_blank"
                rel="noopener noreferrer"
                className="underline"
              >
                openrouter.ai/keys
              </a>
            </p>
          </div>

          <div className="p-3 bg-muted/50 rounded-lg space-y-2">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 mt-0.5 text-muted-foreground" />
              <div className="text-xs text-muted-foreground space-y-1">
                <p>
                  <strong>Privacy:</strong> Your API key is stored locally in
                  your browser and sent directly to the backend.
                </p>
                <p>
                  <strong>Cost:</strong> You'll be charged directly by
                  OpenRouter based on usage.
                </p>
                <p>
                  <strong>Models:</strong> Defaults to Gemini Flash 1.5 (very
                  cheap).
                </p>
              </div>
            </div>
          </div>

          {saved && (
            <div className="text-sm text-green-600 dark:text-green-400">
              ✓ API key saved successfully!
            </div>
          )}
        </div>

        <AlertDialogFooter>
          <Button variant="outline" onClick={handleClear}>
            Clear
          </Button>
          <Button onClick={handleSave} disabled={!apiKey.trim()}>
            Save Key
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
