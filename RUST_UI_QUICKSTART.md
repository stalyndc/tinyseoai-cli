# 🚀 Rust UI Quick Start Guide

Get up and running with TinySEO AI's Rust-powered interfaces in minutes!

## ⚡ 60-Second Quick Start

### Interactive TUI (Terminal UI)

```bash
# 1. Build (one-time setup)
cd rust-ui
cargo build --release

# 2. Run
cd ..
./tinyseoai-ui https://example.com
```

**That's it!** Your interactive dashboard will launch automatically.

### Tauri Desktop App

```bash
# 1. Install dependencies (one-time)
cd tauri-ui
npm install

# 2. Run in dev mode
npm run tauri:dev
```

**Done!** The desktop app will open with hot-reload enabled.

---

## 📋 Prerequisites Check

Before starting, verify you have:

### For TUI:
```bash
# Check Rust
cargo --version
# Should show: cargo 1.70.0 or higher

# Check Python CLI
tinyseoai --version
# Should show: tinyseoai version x.x.x
```

### For Tauri (additional):
```bash
# Check Node.js
node --version
# Should show: v18.0.0 or higher

npm --version
# Should show: 9.0.0 or higher
```

### Missing Prerequisites?

#### Install Rust:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

#### Install Python CLI:
```bash
pip install tinyseoai
```

#### Install Node.js (for Tauri):
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS
brew install node

# Windows
# Download from: https://nodejs.org/
```

---

## 🎯 Usage Examples

### Interactive TUI

#### Basic Usage
```bash
./tinyseoai-ui https://example.com
```

#### Advanced: Audit Multiple Sites
```bash
#!/bin/bash
for site in site1.com site2.com site3.com; do
    ./tinyseoai-ui https://$site
done
```

#### Over SSH
```bash
ssh user@server 'cd tinyseoai-cli && ./tinyseoai-ui https://example.com'
```

### Keyboard Navigation

Once the TUI is running:

```
┌─────────────────────────────────────┐
│ Tab        → Switch between tabs    │
│ Shift+Tab  → Previous tab           │
│ ↑ or k     → Move up                │
│ ↓ or j     → Move down              │
│ PgUp       → Scroll up              │
│ PgDn       → Scroll down            │
│ q or Esc   → Quit                   │
└─────────────────────────────────────┘
```

---

### Tauri Desktop App

#### Development Mode
```bash
cd tauri-ui
npm run tauri:dev
```

**Features in dev mode:**
- 🔥 Hot-reload (changes reflect instantly)
- 🔧 DevTools available (right-click → Inspect)
- 📝 Console logging

#### Production Build
```bash
cd tauri-ui
npm run tauri:build
```

**Output location:**
- macOS: `src-tauri/target/release/bundle/macos/`
- Windows: `src-tauri/target/release/bundle/msi/`
- Linux: `src-tauri/target/release/bundle/deb/` or `.AppImage`

#### Using the App

1. **Launch the app**
2. **Enter URL**: Type or paste website URL
3. **Choose mode**:
   - ⚡ Basic (5-10 sec)
   - 🔍 Full (30-60 sec)
   - 🤖 AI (1-3 min)
4. **Click "Run SEO Audit"**
5. **View results** in real-time

---

## 🎨 Visual Guide

### TUI Layout

```
┌─────────────────────── TinySEO AI ──────────────────────┐
│          🚀 TinySEO AI - Interactive Dashboard          │
│              Analyzing: https://example.com             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Progress: ████████████████░░░░ 80% (16/20 pages)       │
│                                                          │
├─────────────────────────────────────────────────────────┤
│ [📊 Overview] [⚠️  Issues] [💡 Analysis]               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📊 Metrics                                             │
│  ┌──────────────────┬────────────┐                     │
│  │ Pages Scanned    │ 15         │                     │
│  │ Total Issues     │ 27         │                     │
│  │ Critical Issues  │ 5          │  ← High priority!  │
│  │ Warnings         │ 12         │                     │
│  │ Health Score     │ 73%        │                     │
│  └──────────────────┴────────────┘                     │
│                                                          │
│  🎯 Overall Health                                      │
│  ████████████████████░░░░░░░░░░ 73%                    │
│                                                          │
├─────────────────────────────────────────────────────────┤
│ Tab: Switch | ↑↓: Navigate | PgUp/Dn: Scroll | q: Quit │
└─────────────────────────────────────────────────────────┘
```

### Tauri App Interface

```
┌─────────────────────────────────────────────────────┐
│                   🚀 TinySEO AI                     │
│           Professional SEO Audit Dashboard          │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Website URL                                         │
│  ┌────────────────────────────────────────────┐    │
│  │ https://example.com                        │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  Audit Mode                                          │
│  ┌─────────┬─────────┬─────────┐                   │
│  │ ⚡ Basic│ 🔍 Full │ 🤖 AI  │                   │
│  │Fast scan│Compreh..│Smart    │                   │
│  └─────────┴─────────┴─────────┘                   │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │         🚀 Run SEO Audit                   │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 🛠️ Troubleshooting

### Common Issues & Fixes

#### ❌ "cargo: command not found"
```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

#### ❌ "tinyseoai: command not found"
```bash
# Install Python CLI
pip install tinyseoai

# Verify
which tinyseoai
tinyseoai --version
```

#### ❌ TUI: "linking with cc failed"
```bash
# Linux
sudo apt-get install build-essential libssl-dev pkg-config

# macOS
xcode-select --install
```

#### ❌ Tauri: "webkit2gtk not found"
```bash
# Linux only
sudo apt-get install webkit2gtk-4.0 libgtk-3-dev libappindicator3-dev
```

#### ❌ TUI: No colors displaying
```bash
# Set proper terminal
export TERM=xterm-256color

# Test colors
echo -e "\e[31mRed\e[0m \e[32mGreen\e[0m \e[34mBlue\e[0m"
```

#### ❌ Tauri: Build fails on macOS
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Accept license
sudo xcodebuild -license accept
```

---

## 📊 Performance Tips

### TUI Performance

**Faster builds:**
```bash
# Use parallel compilation
cargo build --release -j$(nproc)
```

**Smaller binary:**
```bash
# Strip symbols (already done in release)
strip rust-ui/target/release/tinyseoai-tui
```

### Tauri Performance

**Faster dev startup:**
```bash
# Use Vite's faster mode
npm run dev -- --force
```

**Smaller app bundle:**
```bash
# Production build is already optimized
# But you can additionally:
npm run tauri:build -- --bundles app  # macOS only .app, no .dmg
```

---

## 🎓 Learning Resources

### Understanding the Code

**TUI Architecture:**
```
rust-ui/
├── src/
│   ├── main.rs      → Entry point, event loop
│   └── ui.rs        → UI rendering, state management
├── Cargo.toml       → Dependencies
└── target/release/  → Compiled binary
```

**Tauri Architecture:**
```
tauri-ui/
├── src-tauri/
│   ├── src/
│   │   └── main.rs  → Rust backend, CLI bridge
│   ├── tauri.conf.json → App configuration
│   └── Cargo.toml   → Rust dependencies
├── index.html       → Frontend UI
├── package.json     → Node dependencies
└── vite.config.js   → Build configuration
```

### Key Technologies

- **Ratatui**: TUI framework ([ratatui.rs](https://ratatui.rs))
- **Tauri**: Desktop framework ([tauri.app](https://tauri.app))
- **Crossterm**: Terminal library
- **Tokio**: Async runtime

---

## 🚀 Next Steps

### After Basic Setup

1. **Read the full guide**: [UI_GUIDE.md](UI_GUIDE.md)
2. **Explore agents**: [AGENTS_README.md](AGENTS_README.md)
3. **Customize colors**: Edit `rust-ui/src/ui.rs`
4. **Build for production**: Create distributable apps

### Contributing

Want to improve the UI?

```bash
# Fork the repo
git clone https://github.com/YOUR_USERNAME/tinyseoai-cli.git

# Make changes
cd rust-ui
# Edit src/ui.rs or src/main.rs

# Test
cargo build --release
./target/release/tinyseoai-tui https://example.com

# Submit PR
git commit -am "Improve TUI color scheme"
git push origin your-branch
```

---

## 📞 Need Help?

### Quick Links

- 📖 **Full UI Guide**: [UI_GUIDE.md](UI_GUIDE.md)
- 🐛 **Report Issues**: [GitHub Issues](https://github.com/stalyndc/tinyseoai-cli/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/stalyndc/tinyseoai-cli/discussions)
- 📧 **Email**: support@tinyseoai.com

### Debug Logs

**TUI debugging:**
```bash
# Enable verbose logging
RUST_LOG=debug ./tinyseoai-ui https://example.com
```

**Tauri debugging:**
```bash
# Run with console logs
npm run tauri:dev
# Then: Right-click in app → Inspect → Console
```

---

## ✨ Tips & Tricks

### TUI Power User Tips

1. **Vim users**: Use `j`/`k` for navigation
2. **Quick exit**: Press `q` anytime
3. **SSH-friendly**: Works perfectly over SSH
4. **Tmux integration**: Detach/reattach anytime
5. **Script it**: Use in bash loops for batch audits

### Tauri Power User Tips

1. **DevTools**: Right-click → Inspect (dev mode)
2. **Keyboard shortcuts**: `Cmd/Ctrl+R` to reload
3. **Multiple windows**: Can open multiple instances
4. **Auto-updates**: Can be configured for production
5. **Deep linking**: Can handle custom URL protocols

---

**Ready to audit? Let's go! 🚀**

```bash
# TUI
./tinyseoai-ui https://your-awesome-site.com

# Tauri
cd tauri-ui && npm run tauri:dev
```
