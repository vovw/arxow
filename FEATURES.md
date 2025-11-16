# Arxow Features Guide

## Table of Contents
- [arXiv URL Auto-Fetch](#arxiv-url-auto-fetch)
- [Three-Pass Analysis](#three-pass-analysis)
- [Deep Research Q&A](#deep-research-qa)
- [Citation Extraction](#citation-extraction)
- [Export Options](#export-options)
- [Paper Library](#paper-library)
- [Vim Keybindings](#vim-keybindings)
- [Dark Mode](#dark-mode)

## arXiv URL Auto-Fetch

The fastest way to analyze papers - just paste a URL!

### How It Works
1. Click the "From arXiv URL" tab
2. Paste any arXiv URL or just the paper ID
3. Press Enter or click "Fetch"
4. Paper downloads automatically from arXiv
5. Processing begins immediately

### Supported URL Formats
- **Full URL**: `https://arxiv.org/abs/2301.12345`
- **PDF URL**: `https://arxiv.org/pdf/2301.12345.pdf`
- **With version**: `https://arxiv.org/abs/2301.12345v1`
- **Just the ID**: `2301.12345`
- **Without https**: `arxiv.org/abs/2301.12345`

### Benefits
- **Zero friction**: No need to download PDFs manually
- **One-step process**: From URL to analysis in seconds
- **Always latest**: Fetches directly from arXiv
- **Auto-saved**: Papers saved to library with arXiv metadata
- **Error handling**: Clear messages if URL is invalid

### Example Workflow
```
1. Find interesting paper on arXiv
2. Copy URL from browser
3. Paste into Arxow
4. Press Enter
5. Paper analyzed in ~30 seconds!
```

### Tips
- You can paste the URL with or without `https://`
- Version numbers (like `v1`) are automatically handled
- Works with both `/abs/` and `/pdf/` URLs
- The paper ID alone (like `2301.12345`) is enough
- Fetched papers appear in your library like uploaded ones

## Three-Pass Analysis

Based on the paper ["How to Read a Paper"](http://ccr.sigcomm.org/online/files/p83-keshavA.pdf) by S. Keshav, Arxow implements a structured three-pass approach to understanding research papers.

### First Pass (5-10 minutes) - Press `1`
**Goal**: Get a bird's-eye view of the paper

The first pass analysis provides:
- **Category**: Type of paper (theoretical, experimental, survey, etc.)
- **Context**: Related work and theoretical foundations
- **Correctness**: Whether assumptions appear valid
- **Main Contributions**: 3-5 key contributions
- **Clarity Rating**: How well-written the paper is (1-10)
- **Key Findings**: Most important results
- **Problems Solved**: What real-world problems this addresses
- **Target Audience**: Who would benefit from reading this
- **Read Further**: Whether you should invest more time

**When to use**: Quickly decide if a paper is relevant to your research.

### Second Pass (Up to 1 hour) - Press `2`
**Goal**: Grasp the paper's content without diving into details

The second pass provides:
- **Critical Figures**: 1-3 most important diagrams and why they matter
- **Methodology**: High-level approach and how it works
- **Key Equations**: Important mathematical formulations
- **Experimental Setup**: Datasets, benchmarks, and baselines
- **Main Results**: Summary of experimental outcomes
- **Important Tables**: Critical evaluation data
- **References to Read**: 3-5 papers you should read next
- **Content Understood**: Whether you grasp the paper's flow

**When to use**: Understand the paper well enough to explain it to others.

### Third Pass (1-5 hours) - Press `3`
**Goal**: Virtually re-implement the paper from scratch

The third pass provides:
- **Re-implementation Requirements**: What you'd need to rebuild this
  - Key algorithms
  - Data structures
  - Computational resources
  - Estimated complexity
- **Strong Points**: Greatest strengths of the work
- **Weak Points**: Problematic assumptions and limitations
- **Reproducibility Assessment**:
  - Can it be reproduced?
  - What information is missing?
  - Are code/data available?
- **Innovation Assessment**:
  - What's truly novel vs. incremental
  - Significance to the field
- **Future Work**: Promising research directions
- **Presentation Improvements**: How the paper could be better
- **Overall Quality**: Rating out of 10
- **Recommendation**: Reject/Weak Accept/Accept/Strong Accept

**When to use**: Deeply understand a paper for implementation, review, or building upon it.

## Deep Research Q&A

Ask specific questions about any uploaded paper and get AI-powered answers.

### How It Works
1. Upload and analyze a paper
2. Enter your question in the "Deep Research Q&A" box
3. Press Enter or click "Ask"
4. Receive a detailed answer based on the paper's content

### Example Questions
- "What datasets were used in the experiments?"
- "How does this approach differ from previous work?"
- "What are the computational requirements?"
- "Can you explain the key equation in section 3?"
- "What are the main limitations of this approach?"
- "How could this be applied to [your specific problem]?"

### Tips
- Be specific in your questions
- Reference specific sections if needed
- Ask follow-up questions to dig deeper
- The AI will indicate if the paper doesn't contain relevant information

## Citation Extraction

Automatically extract and analyze all references from a paper.

### Features
- **Full Reference List**: All cited papers with authors, titles, venues
- **Key References**: Most important citations highlighted
- **Relevance Analysis**: Why each paper was cited
- **Citation Count**: Total number of references

### Use Cases
- Build a reading list of related papers
- Understand the paper's theoretical foundations
- Trace the evolution of ideas in a field
- Identify seminal works in an area

## Export Options

Save your analysis for later reference or sharing.

### Export Formats

**Markdown (.md)**
- Human-readable format
- Perfect for note-taking apps (Obsidian, Notion, etc.)
- Includes all analysis passes with formatting
- Contains metadata summary

**JSON (.json)**
- Machine-readable format
- Complete analysis data structure
- Easy to parse programmatically
- Suitable for further processing

### How to Export
1. Complete at least one analysis pass
2. Click "Export" button or press `e`
3. Choose your format (Markdown or JSON)
4. File downloads automatically

## Paper Library

Your recently analyzed papers are saved locally for quick access.

### Features
- **Auto-Save**: Papers saved automatically after upload
- **Quick Load**: Click "Load" to re-open any recent paper
- **Metadata Preview**: See filename and upload time
- **Storage**: Keeps last 10 papers (localStorage)
- **Privacy**: All data stays on your device

### Managing Your Library
- Papers are sorted by most recent first
- Click trash icon to remove a paper
- Library persists across browser sessions
- No account or login required

## Vim Keybindings

Power user? Arxow includes full vim-style keyboard navigation.

### Navigation
- `j` - Scroll down (like vim)
- `k` - Scroll up (like vim)
- `g` - Jump to top of page (like vim `gg`)
- `G` - Jump to bottom of page (like vim `G`)

### Actions
- `1` - Run First Pass analysis
- `2` - Run Second Pass analysis
- `3` - Run Third Pass analysis
- `e` - Export analysis
- `Shift+D` - Toggle dark/light mode
- `?` - Show keyboard shortcuts help

### Tips
- Shortcuts work globally (except when typing in inputs)
- Press `?` anytime to see all shortcuts
- Disable vim mode in settings if preferred
- Combine with mouse/trackpad for hybrid workflow

## Dark Mode

Beautiful dark theme that's easy on the eyes.

### Features
- **Auto-Save**: Theme preference saved locally
- **Smooth Transition**: Animated theme switching
- **Custom Palette**: Carefully chosen dark colors
- **Code Syntax**: Enhanced dark theme for code blocks
- **Accessibility**: Meets WCAG contrast requirements

### Toggle Methods
1. Click sun/moon icon in header
2. Press `Shift+D` keyboard shortcut
3. Preference saved automatically

### Color Scheme
- **Background**: Deep charcoal (#0a0a0a)
- **Foreground**: Soft white (#fafafa)
- **Accent**: Muted colors for reduced eye strain
- **Borders**: Subtle separators
- **Code**: Syntax highlighting optimized for dark mode

## Keyboard Shortcuts Reference

Press `?` to see this in-app:

| Shortcut | Action |
|----------|--------|
| `1` | First Pass Analysis |
| `2` | Second Pass Analysis |
| `3` | Third Pass Analysis |
| `j` | Scroll Down |
| `k` | Scroll Up |
| `g` | Jump to Top |
| `G` | Jump to Bottom |
| `Shift+D` | Toggle Dark Mode |
| `e` | Export Analysis |
| `?` | Show Keyboard Help |
| `ESC` | Close Modals |

## Best Practices

### Efficient Workflow
1. **First Pass Everything**: Quickly scan all potentially relevant papers
2. **Second Pass Selected**: Deep dive into the most relevant papers
3. **Third Pass Few**: Only for papers you'll implement or build upon
4. **Ask Questions**: Use Deep Research Q&A when confused
5. **Export Important**: Save analysis of key papers for reference

### Organization Tips
- Export important analyses to your notes app
- Use citation extraction to build reading lists
- Keep paper library clean (delete old analyses)
- Take notes while analyzing in your preferred tool

### Performance Tips
- Upload papers once, analyze multiple times (cached)
- First pass is fastest (~30 seconds)
- Third pass takes longest (~2-3 minutes)
- Deep Research Q&A is nearly instant
- Export is instant (client-side only)

## Coming Soon

Features in development:
- Paper comparison tool
- Citation graph visualization
- Batch processing
- Custom analysis prompts
- Local LLM support
- Browser extension
- Mobile app
