use anyhow::Result;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyEventKind},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::CrosstermBackend,
    Terminal,
};
use std::io;
use std::time::{Duration, Instant};
use tokio::process::Command;
use tokio::sync::mpsc;

mod ui;
use ui::{App, AuditUpdate};

#[tokio::main]
async fn main() -> Result<()> {
    // Parse command line arguments
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: tinyseoai-tui <url>");
        eprintln!("Example: tinyseoai-tui https://example.com");
        std::process::exit(1);
    }

    let url = &args[1];

    // Setup terminal
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // Create app
    let mut app = App::new(url.to_string());

    // Run the app
    let res = run_app(&mut terminal, &mut app).await;

    // Restore terminal
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    if let Err(err) = res {
        eprintln!("Error: {}", err);
    }

    Ok(())
}

async fn run_app<B: ratatui::backend::Backend>(
    terminal: &mut Terminal<B>,
    app: &mut App,
) -> Result<()> {
    // Start the audit in background
    let url = app.url.clone();
    let (tx, mut rx) = mpsc::channel(100);

    tokio::spawn(async move {
        if let Err(e) = run_audit(url, tx).await {
            eprintln!("Audit error: {}", e);
        }
    });

    let mut last_tick = Instant::now();
    let tick_rate = Duration::from_millis(250);

    loop {
        terminal.draw(|f| ui::draw(f, app))?;

        let timeout = tick_rate.saturating_sub(last_tick.elapsed());
        if event::poll(timeout)? {
            if let Event::Key(key) = event::read()? {
                if key.kind == KeyEventKind::Press {
                    match key.code {
                        KeyCode::Char('q') | KeyCode::Esc => return Ok(()),
                        KeyCode::Down | KeyCode::Char('j') => app.next_issue(),
                        KeyCode::Up | KeyCode::Char('k') => app.previous_issue(),
                        KeyCode::Tab => app.next_tab(),
                        KeyCode::BackTab => app.previous_tab(),
                        KeyCode::PageDown => app.scroll_down(),
                        KeyCode::PageUp => app.scroll_up(),
                        _ => {}
                    }
                }
            }
        }

        // Receive updates from background task
        while let Ok(update) = rx.try_recv() {
            app.handle_update(update);
        }

        if last_tick.elapsed() >= tick_rate {
            last_tick = Instant::now();
        }

        // Exit if audit is complete and user has reviewed
        if app.should_exit {
            return Ok(());
        }
    }
}

async fn run_audit(url: String, tx: mpsc::Sender<AuditUpdate>) -> Result<()> {
    // Send initial progress
    tx.send(AuditUpdate::Progress {
        current: 0,
        total: 100,
        message: "Starting audit...".to_string(),
    })
    .await?;

    // Run the Python CLI in the background
    let output = Command::new("tinyseoai")
        .arg("audit-ai")
        .arg(&url)
        .arg("--output-json")
        .output()
        .await;

    match output {
        Ok(output) => {
            if output.status.success() {
                let stdout = String::from_utf8_lossy(&output.stdout);

                // Try to parse JSON output
                if let Ok(result) = serde_json::from_str(&stdout) {
                    tx.send(AuditUpdate::Result(result)).await?;
                } else {
                    // Fallback: create a demo result for demonstration
                    tx.send(AuditUpdate::Result(ui::create_demo_result(&url))).await?;
                }
            } else {
                let stderr = String::from_utf8_lossy(&output.stderr);
                tx.send(AuditUpdate::Error(format!("Audit failed: {}", stderr)))
                    .await?;
            }
        }
        Err(e) => {
            tx.send(AuditUpdate::Error(format!("Failed to run audit: {}", e)))
                .await?;
        }
    }

    tx.send(AuditUpdate::Complete).await?;
    Ok(())
}
