/** Consumer palette approved 7 September 2026. Generate with node scripts/build-skins.mjs. */
export const CAT_HUES = {
  "organize": 210,
  "edit": 265,
  "optimize": 175,
  "security": 350,
  "to-pdf": 150,
  "from-pdf": 32,
  "advanced": 240,
  "image": 320,
  "video": 12,
  "developer": 190,
  "archive": 45,
  "document": 95
};

export const SKINS = {
  "daylight": {
    "label": "Daylight",
    "fonts": {
      "display": "'Bricolage Grotesque', system-ui, sans-serif",
      "sans": "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      "mono": "'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace"
    },
    "radius": "0.75rem",
    "cat": {
      "s": 52,
      "l": {
        "dark": 64,
        "light": 40
      }
    },
    "dark": {
      "ground": "#050D18",
      "core": {
        "background": "#050D18",
        "foreground": "#F4F6FA",
        "paper": "#0C1623",
        "paper-2": "#111D2C",
        "paper-3": "#192638",
        "card": "#0C1623",
        "card-foreground": "#F4F6FA",
        "card-tint": "#101C2B",
        "popover": "#0C1623",
        "popover-foreground": "#F4F6FA",
        "primary": "#6596FF",
        "primary-foreground": "#071325",
        "secondary": "#172438",
        "secondary-foreground": "#F4F6FA",
        "muted": "#101C2B",
        "muted-foreground": "#B7C2D3",
        "accent": "#6596FF",
        "accent-bright": "#6596FF",
        "accent-foreground": "#071325",
        "copper": "#E0736B",
        "success": "#8EDBAD",
        "destructive": "#E0736B",
        "destructive-foreground": "#0F1113",
        "ring": "#6596FF"
      },
      "alpha": {
        "border": [
          "rgba(203,217,240,.19)"
        ],
        "border-strong": [
          "rgba(203,217,240,.35)"
        ],
        "input": [
          "rgba(203,217,240,.25)"
        ],
        "accent-soft": [
          "rgba(101,150,255,.13)"
        ],
        "copper-soft": [
          "rgba(224,115,107,.12)"
        ],
        "success-soft": [
          "rgba(56,211,146,.13)"
        ]
      },
      "raw": {
        "rail": "#0C1623",
        "scrim": "rgba(0,0,0,.7)",
        "hero-bg": "#050D18",
        "panel-glass": "rgba(23,26,29,.85)",
        "edge": "rgba(101,150,255,.3)",
        "edge-soft": "rgba(101,150,255,.12)",
        "edge-hot": "rgba(101,150,255,.5)",
        "halo": "transparent",
        "halo-2": "transparent",
        "sheen": "rgba(255,255,255,.15)",
        "grain-o": "0",
        "glass-blur": "0px",
        "glass-a": "rgba(56,211,146,.07)",
        "primary-glow": "transparent",
        "shadow-panel": "0 24px 56px -20px rgba(0,0,0,.7)"
      }
    },
    "light": {
      "ground": "#FFFFFF",
      "core": {
        "background": "#FFFFFF",
        "foreground": "#0B0D12",
        "paper": "#FFFFFF",
        "paper-2": "#F5F7FB",
        "paper-3": "#EEF2F8",
        "card": "#FFFFFF",
        "card-foreground": "#0B0D12",
        "card-tint": "#F7F9FC",
        "popover": "#FFFFFF",
        "popover-foreground": "#0B0D12",
        "primary": "#0052FF",
        "primary-foreground": "#FFFFFF",
        "secondary": "#EFF3F9",
        "secondary-foreground": "#0B0D12",
        "muted": "#F5F7FB",
        "muted-foreground": "#566174",
        "accent": "#0052FF",
        "accent-bright": "#0052FF",
        "accent-foreground": "#FFFFFF",
        "copper": "#B4443C",
        "success": "#157347",
        "destructive": "#B4443C",
        "destructive-foreground": "#FFFFFF",
        "ring": "#0052FF"
      },
      "alpha": {
        "border": [
          "rgba(29,51,90,.17)"
        ],
        "border-strong": [
          "rgba(29,51,90,.32)"
        ],
        "input": [
          "rgba(29,51,90,.24)"
        ],
        "accent-soft": [
          "rgba(0,82,255,.045)"
        ],
        "copper-soft": [
          "rgba(180,68,60,.10)"
        ],
        "success-soft": [
          "rgba(12,126,86,.12)"
        ]
      },
      "raw": {
        "rail": "#F5F7FB",
        "scrim": "rgba(10,12,13,.5)",
        "hero-bg": "#FFFFFF",
        "panel-glass": "rgba(255,255,255,.85)",
        "edge": "rgba(0,82,255,.3)",
        "edge-soft": "rgba(0,82,255,.12)",
        "edge-hot": "rgba(0,82,255,.5)",
        "halo": "transparent",
        "halo-2": "transparent",
        "sheen": "rgba(255,255,255,.6)",
        "grain-o": "0",
        "glass-blur": "0px",
        "glass-a": "rgba(12,126,86,.06)",
        "primary-glow": "transparent",
        "shadow-panel": "0 28px 64px -24px rgba(16,20,22,.2)"
      }
    }
  }
};
