# TinySEO AI - User Interface Guide

Welcome to the TinySEO AI UI Guide! This document covers all the user interfaces available for TinySEO AI.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Interactive TUI (Terminal UI)](#interactive-tui)
3. [Tauri Desktop App](#tauri-desktop-app)
4. [Original CLI](#original-cli)
5. [Installation](#installation)
6. [Troubleshooting](#troubleshooting)

---

## 🌟 Overview

TinySEO AI now offers **three different interfaces** to suit your workflow:

| Interface | Best For | Features |
|-----------|----------|----------|
| **🖥️ Interactive TUI** | Terminal users, SSH, CI/CD | Real-time dashboard, keyboard navigation |
| **🪟 Tauri Desktop App** | Desktop users, visual preference | Native performance, modern UI |
| **⌨️ Original CLI** | Scripts, automation, power users | JSON output, pipe-friendly |

---

## 🖥️ Interactive TUI (Terminal UI)

### What is it?

A beautiful, **interactive terminal-based dashboard** built with Rust and Ratatui. Think of it as a full-featured GUI that runs in your terminal!

### Features

- ✨ **Real-time progress tracking** with live updates
- 📊 **Interactive dashboard** with multiple tabs
- ⚡ **Keyboard navigation** (Vim-style shortcuts supported)
- 🎨 **Beautiful colored output** with tables and charts
- 📈 **Live metrics** during audit execution
- 🔍 **Detailed issue browser** with scrolling

### Installation

#### Prerequisites

```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

#### Build the TUI

```bash
cd rust-ui
cargo build --release
```

The binary will be available at: `rust-ui/target/release/tinyseoai-tui`

### Usage

#### Using the launcher script

```bash
# Make the launcher executable (first time only)
chmod +x tinyseoai-ui

# Run audit
./tinyseoai-ui https://example.com
```

#### Direct execution

```bash
./rust-ui/target/release/tinyseoai-tui https://example.com
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Tab` | Switch between tabs |
| `Shift+Tab` | Previous tab |
| `↑` or `k` | Move up in list |
| `↓` or `j` | Move down in list |
| `PgUp` | Scroll up |
| `PgDn` | Scroll down |
| `q` or `Esc` | Quit |

### UI Layout

```
┌─────────────────────── TinySEO AI ───────────────────────┐
│ URL: example.com              Status: ⚡ Analyzing...     │
├──────────────────────────────────────────────────────────┤
│ Progress: ████████████░░░░░░░░ 65% (13/20 pages)        │
├──────────────────────────────────────────────────────────┤
│ 📊 Overview | ⚠️ Issues | 💡 Analysis                   │
├──────────────────────────────────────────────────────────┤
│ [Content based on selected tab]                          │
│                                                           │
│ • Overview: Metrics, health score, summary               │
│ • Issues: Detailed list with recommendations             │
│ • Analysis: AI-powered insights                          │
└──────────────────────────────────────────────────────────┘
│ Tab: Switch | ↑↓: Navigate | PgUp/Dn: Scroll | q: Quit  │
└──────────────────────────────────────────────────────────┘
```

### Tabs Explained

#### 📊 Overview Tab

Displays:
- **Pages Scanned**: Total pages analyzed
- **Issues Summary**: Critical, warnings, and info
- **Health Score**: Overall site health (0-100%)
- **Visual Gauge**: Color-coded health indicator
  - 🟢 Green: 90-100% (Excellent)
  - 🟡 Yellow: 70-89% (Good)
  - 🔴 Red: 0-69% (Needs Attention)

#### ⚠️ Issues Tab

**Left Panel**: Issue list
- 🔴 Critical issues (requires immediate attention)
- 🟡 Warnings (should be addressed)
- 🔵 Info (nice to have)

**Right Panel**: Selected issue details
- Severity level
- Description
- Affected pages
- Recommendations

**Navigation**: Use ↑↓ or j/k to browse issues

#### 💡 Analysis Tab

Shows AI-generated analysis and recommendations based on:
- Overall site structure
- Content quality
- Technical SEO factors
- Performance metrics

---

## 🪟 Tauri Desktop App

### What is it?

A **native desktop application** built with Tauri and Rust. Lightweight, fast, and provides a modern web-based UI with native performance.

### Features

- 🚀 **Native desktop app** for Windows, macOS, and Linux
- 💻 **Modern web UI** with beautiful design
- ⚡ **Rust backend** for superior performance
- 📦 **Small bundle size** (~3MB vs 150MB for Electron)
- 🔒 **Secure** with built-in security features
- 🎯 **Three audit modes**: Basic, Full, AI-Powered

### Installation

#### Prerequisites

```bash
# Install Node.js (if not already installed)
# Visit: https://nodejs.org/ or use:
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

#### Install Dependencies

```bash
cd tauri-ui
npm install
```

### Running in Development Mode

```bash
cd tauri-ui
npm run tauri:dev
```

This will:
1. Start the Vite dev server
2. Launch the Tauri app
3. Enable hot-reload for development

### Building for Production

```bash
cd tauri-ui
npm run tauri:build
```

The built application will be in: `tauri-ui/src-tauri/target/release/`

Platform-specific installers will be generated:
- **macOS**: `.dmg`, `.app`
- **Windows**: `.msi`, `.exe`
- **Linux**: `.deb`, `.AppImage`

### Usage

1. **Launch the app**
2. **Enter a URL** in the input field
3. **Select audit mode**:
   - ⚡ **Basic**: Fast scan of essential SEO factors
   - 🔍 **Full**: Comprehensive analysis of all aspects
   - 🤖 **AI-Powered**: Multi-agent AI analysis (requires API keys)
4. **Click "Run SEO Audit"**
5. **View results** in real-time

### UI Features

#### Audit Modes

```
┌─────────────────────────────────────────────┐
│ ⚡ Basic       │ 🔍 Full       │ 🤖 AI      │
│ Fast scan     │ Comprehensive │ Smart       │
└─────────────────────────────────────────────┘
```

- **Basic**: 5-10 seconds, covers essentials
- **Full**: 30-60 seconds, deep analysis
- **AI-Powered**: 1-3 minutes, intelligent recommendations

#### Results Display

- ✅ **Success badge** with status
- 📊 **Formatted output** with syntax highlighting
- 📋 **Copy-friendly** results
- ❌ **Error messages** with troubleshooting tips

---

## ⌨️ Original CLI

The original command-line interface is still available for automation and scripting.

### Usage

```bash
# Basic audit
tinyseoai audit https://example.com

# Full audit
tinyseoai audit-full https://example.com

# AI-powered audit
tinyseoai audit-ai https://example.com

# Generate report
tinyseoai report audit_results.json
```

See the main [README.md](README.md) for full CLI documentation.

---

## 💾 Installation

### System Requirements

#### All Platforms
- **RAM**: 512MB minimum, 2GB recommended
- **Disk Space**: 500MB for tools, 1GB for cache
- **Internet**: Required for audits and AI features

#### Interactive TUI
- **Rust**: 1.70+ (automatically installed)
- **Terminal**: Any modern terminal with 256-color support
- **OS**: Linux, macOS, Windows (WSL recommended)

#### Tauri Desktop App
- **Node.js**: 18+
- **Rust**: 1.70+
- **OS-Specific**:
  - **Linux**: `webkit2gtk`, `libssl-dev`, `libgtk-3-dev`
  - **macOS**: Xcode Command Line Tools
  - **Windows**: WebView2 (usually pre-installed)

### Step-by-Step Installation

#### 1. Install TinySEO CLI (Required for all UIs)

```bash
pip install tinyseoai
```

#### 2. Install Rust (Required for TUI and Tauri)

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

#### 3. Build Interactive TUI

```bash
cd rust-ui
cargo build --release
```

#### 4. Set up Tauri (Optional)

```bash
# Install Node.js first, then:
cd tauri-ui
npm install
npm run tauri:build
```

### Quick Start Scripts

#### For TUI Users

```bash
# Clone and build
git clone https://github.com/stalyndc/tinyseoai-cli.git
cd tinyseoai-cli
cd rust-ui && cargo build --release && cd ..
chmod +x tinyseoai-ui

# Run
./tinyseoai-ui https://example.com
```

#### For Tauri Users

```bash
# Clone and build
git clone https://github.com/stalyndc/tinyseoai-cli.git
cd tinyseoai-cli/tauri-ui
npm install
npm run tauri:dev
```

---

## 🔧 Troubleshooting

### Interactive TUI Issues

#### Error: "tinyseoai: command not found"

**Solution**: Install the Python CLI first:
```bash
pip install tinyseoai
```

#### Error: "cannot find -lssl"

**Solution** (Linux):
```bash
sudo apt-get install libssl-dev pkg-config
```

#### TUI doesn't display colors

**Solution**: Ensure your terminal supports 256 colors:
```bash
echo $TERM  # Should be xterm-256color or similar
export TERM=xterm-256color
```

#### Keyboard shortcuts not working

**Solution**: Make sure you're not in a tmux/screen session that intercepts keys, or remap the shortcuts.

### Tauri App Issues

#### Error: "webkit2gtk not found"

**Solution** (Linux):
```bash
sudo apt-get install webkit2gtk-4.0 libgtk-3-dev
```

#### Error: "npm run tauri:dev" fails

**Solution**: Check Node.js version:
```bash
node --version  # Should be 18+
npm install     # Reinstall dependencies
```

#### App shows "CLI not installed" warning

**Solution**: Install TinySEO CLI:
```bash
pip install tinyseoai
which tinyseoai  # Verify it's in PATH
```

### General Issues

#### Slow audit performance

**Possible causes**:
- Large website (many pages)
- Slow network connection
- Rate limiting by target server

**Solutions**:
- Use Basic mode for faster results
- Check internet connection
- Wait and retry later

#### Out of memory errors

**Solution**: Close other applications or use Basic audit mode.

#### API key errors (AI mode)

**Solution**: Set up API keys:
```bash
cp .env.example .env
# Edit .env and add your OpenAI/Anthropic keys
```

---

## 🎨 Customization

### TUI Color Scheme

Edit `rust-ui/src/ui.rs` to customize colors:

```rust
// Example: Change header color
.fg(Color::Cyan)  // Change to Color::Green, Color::Blue, etc.
```

Rebuild after changes:
```bash
cd rust-ui && cargo build --release
```

### Tauri UI Styling

Edit `tauri-ui/index.html` to customize the web interface:

```css
/* Example: Change gradient */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
/* Change to your preferred colors */
```

---

## 📊 Feature Comparison

| Feature | TUI | Tauri | CLI |
|---------|-----|-------|-----|
| **Speed** | ⚡⚡⚡ | ⚡⚡⚡ | ⚡⚡⚡⚡ |
| **Visual Appeal** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Resource Usage** | 🟢 Low | 🟢 Low | 🟢 Very Low |
| **Ease of Use** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Automation** | ⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ |
| **Remote Access** | ✅ | ❌ | ✅ |
| **Offline Use** | ✅ | ✅ | ✅ |
| **Real-time Updates** | ✅ | ✅ | ❌ |

---

## 🚀 Advanced Usage

### TUI: Running over SSH

```bash
# On remote server
ssh user@server
cd tinyseoai-cli
./tinyseoai-ui https://example.com
```

### TUI: Integration with tmux

```bash
# Create tmux session
tmux new -s audit

# Run TUI
./tinyseoai-ui https://example.com

# Detach: Ctrl+b, d
# Reattach: tmux attach -t audit
```

### Tauri: Automated Builds

```bash
# Build for all platforms (requires platform-specific setup)
cd tauri-ui
npm run tauri:build -- --target all
```

### CLI: JSON Output for Processing

```bash
# Export JSON
tinyseoai audit https://example.com > results.json

# Parse with jq
cat results.json | jq '.issues[] | select(.severity=="critical")'
```

---

## 🆘 Getting Help

### Documentation
- **Main README**: [README.md](README.md)
- **Agents Guide**: [AGENTS_README.md](AGENTS_README.md)
- **Quick Start**: [QUICK_START.md](QUICK_START.md)

### Community
- **Issues**: [GitHub Issues](https://github.com/stalyndc/tinyseoai-cli/issues)
- **Discussions**: [GitHub Discussions](https://github.com/stalyndc/tinyseoai-cli/discussions)

### Contact
- **Email**: support@tinyseoai.com
- **Website**: https://tinyseoai.com

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Happy auditing! 🚀**
