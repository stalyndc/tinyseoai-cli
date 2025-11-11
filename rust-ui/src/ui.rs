use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{
        Block, Borders, Cell, Gauge, List, ListItem, Paragraph, Row, Table,
        Tabs, Wrap,
    },
    Frame,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditResult {
    pub url: String,
    pub timestamp: String,
    pub metrics: Metrics,
    pub issues: Vec<Issue>,
    pub analysis: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Metrics {
    pub pages_scanned: usize,
    pub total_issues: usize,
    pub critical_issues: usize,
    pub warnings: usize,
    pub info: usize,
    pub health_score: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Issue {
    pub severity: String,
    pub category: String,
    pub title: String,
    pub description: String,
    pub affected_pages: Vec<String>,
    pub recommendation: String,
}

#[derive(Debug)]
pub enum AppState {
    Loading,
    Running { progress: usize, message: String },
    Complete,
    Error(String),
}

#[derive(Debug)]
pub struct App {
    pub url: String,
    pub state: AppState,
    pub result: Option<AuditResult>,
    pub selected_tab: usize,
    pub selected_issue: usize,
    pub scroll_offset: usize,
    pub should_exit: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum AuditUpdate {
    Progress {
        current: usize,
        total: usize,
        message: String,
    },
    Result(AuditResult),
    Error(String),
    Complete,
}

impl App {
    pub fn new(url: String) -> Self {
        Self {
            url,
            state: AppState::Loading,
            result: None,
            selected_tab: 0,
            selected_issue: 0,
            scroll_offset: 0,
            should_exit: false,
        }
    }

    pub fn handle_update(&mut self, update: AuditUpdate) {
        match update {
            AuditUpdate::Progress {
                current,
                total,
                message,
            } => {
                self.state = AppState::Running {
                    progress: (current * 100 / total.max(1)),
                    message,
                };
            }
            AuditUpdate::Result(result) => {
                self.result = Some(result);
                self.state = AppState::Complete;
            }
            AuditUpdate::Error(err) => {
                self.state = AppState::Error(err);
            }
            AuditUpdate::Complete => {
                if matches!(self.state, AppState::Running { .. }) {
                    self.state = AppState::Complete;
                }
            }
        }
    }

    pub fn next_issue(&mut self) {
        if let Some(result) = &self.result {
            if self.selected_issue < result.issues.len().saturating_sub(1) {
                self.selected_issue += 1;
                self.scroll_offset = 0;
            }
        }
    }

    pub fn previous_issue(&mut self) {
        if self.selected_issue > 0 {
            self.selected_issue -= 1;
            self.scroll_offset = 0;
        }
    }

    pub fn next_tab(&mut self) {
        self.selected_tab = (self.selected_tab + 1) % 3;
        self.scroll_offset = 0;
    }

    pub fn previous_tab(&mut self) {
        self.selected_tab = if self.selected_tab == 0 {
            2
        } else {
            self.selected_tab - 1
        };
        self.scroll_offset = 0;
    }

    pub fn scroll_down(&mut self) {
        self.scroll_offset += 1;
    }

    pub fn scroll_up(&mut self) {
        self.scroll_offset = self.scroll_offset.saturating_sub(1);
    }
}

pub fn draw(f: &mut Frame, app: &App) {
    let size = f.area();

    // Create main layout
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),  // Header
            Constraint::Min(0),     // Content
            Constraint::Length(3),  // Footer
        ])
        .split(size);

    // Draw header
    draw_header(f, chunks[0], app);

    // Draw content based on state
    match &app.state {
        AppState::Loading => draw_loading(f, chunks[1]),
        AppState::Running { progress, message } => {
            draw_progress(f, chunks[1], *progress, message)
        }
        AppState::Complete => {
            if let Some(result) = &app.result {
                draw_results(f, chunks[1], app, result);
            }
        }
        AppState::Error(err) => draw_error(f, chunks[1], err),
    }

    // Draw footer
    draw_footer(f, chunks[2], app);
}

fn draw_header(f: &mut Frame, area: Rect, app: &App) {
    let title = format!("🚀 TinySEO AI - Interactive Dashboard");
    let subtitle = format!("Analyzing: {}", app.url);

    let header = Paragraph::new(vec![
        Line::from(Span::styled(
            title,
            Style::default()
                .fg(Color::Cyan)
                .add_modifier(Modifier::BOLD),
        )),
        Line::from(Span::styled(subtitle, Style::default().fg(Color::Gray))),
    ])
    .block(
        Block::default()
            .borders(Borders::ALL)
            .border_style(Style::default().fg(Color::Cyan)),
    )
    .alignment(Alignment::Center);

    f.render_widget(header, area);
}

fn draw_loading(f: &mut Frame, area: Rect) {
    let loading = Paragraph::new("⏳ Initializing audit...\n\nPlease wait while we set up the environment.")
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Loading")
                .border_style(Style::default().fg(Color::Yellow)),
        )
        .alignment(Alignment::Center)
        .wrap(Wrap { trim: true });

    f.render_widget(loading, area);
}

fn draw_progress(f: &mut Frame, area: Rect, progress: usize, message: &str) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Percentage(50), Constraint::Percentage(50)])
        .split(area);

    let gauge = Gauge::default()
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Audit Progress")
                .border_style(Style::default().fg(Color::Green)),
        )
        .gauge_style(
            Style::default()
                .fg(Color::Green)
                .bg(Color::Black)
                .add_modifier(Modifier::BOLD),
        )
        .percent(progress as u16)
        .label(format!("{}%", progress));

    let status = Paragraph::new(message)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Status")
                .border_style(Style::default().fg(Color::Yellow)),
        )
        .alignment(Alignment::Center)
        .wrap(Wrap { trim: true });

    f.render_widget(gauge, chunks[0]);
    f.render_widget(status, chunks[1]);
}

fn draw_results(f: &mut Frame, area: Rect, app: &App, result: &AuditResult) {
    // Create layout for tabs and content
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Length(3), Constraint::Min(0)])
        .split(area);

    // Draw tabs
    let tabs = Tabs::new(vec!["📊 Overview", "⚠️  Issues", "💡 Analysis"])
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::Cyan)),
        )
        .select(app.selected_tab)
        .style(Style::default().fg(Color::White))
        .highlight_style(
            Style::default()
                .fg(Color::Cyan)
                .add_modifier(Modifier::BOLD),
        );

    f.render_widget(tabs, chunks[0]);

    // Draw content based on selected tab
    match app.selected_tab {
        0 => draw_overview(f, chunks[1], result),
        1 => draw_issues(f, chunks[1], app, result),
        2 => draw_analysis(f, chunks[1], result),
        _ => {}
    }
}

fn draw_overview(f: &mut Frame, area: Rect, result: &AuditResult) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Length(10), Constraint::Min(0)])
        .split(area);

    // Metrics panel
    let metrics = result.metrics.clone();
    let health_color = match metrics.health_score {
        90..=100 => Color::Green,
        70..=89 => Color::Yellow,
        _ => Color::Red,
    };

    let metrics_rows = vec![
        Row::new(vec![
            Cell::from("Pages Scanned"),
            Cell::from(metrics.pages_scanned.to_string()),
        ]),
        Row::new(vec![
            Cell::from("Total Issues"),
            Cell::from(metrics.total_issues.to_string()).style(Style::default().fg(Color::Yellow)),
        ]),
        Row::new(vec![
            Cell::from("Critical Issues"),
            Cell::from(metrics.critical_issues.to_string())
                .style(Style::default().fg(Color::Red).add_modifier(Modifier::BOLD)),
        ]),
        Row::new(vec![
            Cell::from("Warnings"),
            Cell::from(metrics.warnings.to_string()).style(Style::default().fg(Color::Yellow)),
        ]),
        Row::new(vec![
            Cell::from("Info"),
            Cell::from(metrics.info.to_string()).style(Style::default().fg(Color::Blue)),
        ]),
        Row::new(vec![
            Cell::from("Health Score"),
            Cell::from(format!("{}%", metrics.health_score))
                .style(Style::default().fg(health_color).add_modifier(Modifier::BOLD)),
        ]),
    ];

    let metrics_table = Table::new(
        metrics_rows,
        [Constraint::Percentage(50), Constraint::Percentage(50)],
    )
    .block(
        Block::default()
            .borders(Borders::ALL)
            .title("📊 Metrics")
            .border_style(Style::default().fg(Color::Green)),
    )
    .column_spacing(2);

    f.render_widget(metrics_table, chunks[0]);

    // Health score gauge
    let gauge = Gauge::default()
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("🎯 Overall Health")
                .border_style(Style::default().fg(Color::Cyan)),
        )
        .gauge_style(Style::default().fg(health_color).bg(Color::Black))
        .percent(metrics.health_score as u16)
        .label(format!("{}% Health Score", metrics.health_score));

    f.render_widget(gauge, chunks[1]);
}

fn draw_issues(f: &mut Frame, area: Rect, app: &App, result: &AuditResult) {
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(40), Constraint::Percentage(60)])
        .split(area);

    // Issues list
    let issues: Vec<ListItem> = result
        .issues
        .iter()
        .enumerate()
        .map(|(i, issue)| {
            let icon = match issue.severity.as_str() {
                "critical" => "🔴",
                "warning" => "🟡",
                _ => "🔵",
            };
            let style = if i == app.selected_issue {
                Style::default()
                    .bg(Color::DarkGray)
                    .add_modifier(Modifier::BOLD)
            } else {
                Style::default()
            };
            ListItem::new(format!("{} {} - {}", icon, issue.category, issue.title))
                .style(style)
        })
        .collect();

    let issues_list = List::new(issues)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title(format!("⚠️  Issues ({}/{})", app.selected_issue + 1, result.issues.len()))
                .border_style(Style::default().fg(Color::Yellow)),
        )
        .highlight_style(
            Style::default()
                .bg(Color::DarkGray)
                .add_modifier(Modifier::BOLD),
        );

    f.render_widget(issues_list, chunks[0]);

    // Issue details
    if let Some(issue) = result.issues.get(app.selected_issue) {
        let severity_color = match issue.severity.as_str() {
            "critical" => Color::Red,
            "warning" => Color::Yellow,
            _ => Color::Blue,
        };

        let details_text = vec![
            Line::from(vec![
                Span::styled("Severity: ", Style::default().add_modifier(Modifier::BOLD)),
                Span::styled(
                    issue.severity.to_uppercase(),
                    Style::default()
                        .fg(severity_color)
                        .add_modifier(Modifier::BOLD),
                ),
            ]),
            Line::from(""),
            Line::from(vec![Span::styled(
                "Description:",
                Style::default().add_modifier(Modifier::BOLD),
            )]),
            Line::from(issue.description.clone()),
            Line::from(""),
            Line::from(vec![Span::styled(
                "Affected Pages:",
                Style::default().add_modifier(Modifier::BOLD),
            )]),
        ];

        let mut all_lines = details_text;
        for page in &issue.affected_pages {
            all_lines.push(Line::from(format!("  • {}", page)));
        }
        all_lines.push(Line::from(""));
        all_lines.push(Line::from(vec![Span::styled(
            "Recommendation:",
            Style::default()
                .fg(Color::Green)
                .add_modifier(Modifier::BOLD),
        )]));
        all_lines.push(Line::from(issue.recommendation.clone()));

        let details = Paragraph::new(all_lines)
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .title("📝 Details")
                    .border_style(Style::default().fg(Color::Cyan)),
            )
            .wrap(Wrap { trim: true })
            .scroll((app.scroll_offset as u16, 0));

        f.render_widget(details, chunks[1]);
    }
}

fn draw_analysis(f: &mut Frame, area: Rect, result: &AuditResult) {
    let analysis_text = result
        .analysis
        .as_ref()
        .map(|s| s.as_str())
        .unwrap_or("No analysis available yet. Run the AI-powered audit for detailed insights.");

    let analysis = Paragraph::new(analysis_text)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("💡 AI Analysis")
                .border_style(Style::default().fg(Color::Magenta)),
        )
        .wrap(Wrap { trim: true })
        .scroll((0, 0));

    f.render_widget(analysis, area);
}

fn draw_error(f: &mut Frame, area: Rect, error: &str) {
    let error_widget = Paragraph::new(format!("❌ Error:\n\n{}", error))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Error")
                .border_style(Style::default().fg(Color::Red)),
        )
        .style(Style::default().fg(Color::Red))
        .alignment(Alignment::Center)
        .wrap(Wrap { trim: true });

    f.render_widget(error_widget, area);
}

fn draw_footer(f: &mut Frame, area: Rect, app: &App) {
    let help_text = match app.state {
        AppState::Complete => {
            "Tab: Switch tabs | ↑↓/jk: Navigate | PgUp/PgDn: Scroll | q/Esc: Quit"
        }
        _ => "Please wait for audit to complete... | q/Esc: Quit",
    };

    let footer = Paragraph::new(help_text)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::Gray)),
        )
        .style(Style::default().fg(Color::Gray))
        .alignment(Alignment::Center);

    f.render_widget(footer, area);
}

pub fn create_demo_result(url: &str) -> AuditResult {
    AuditResult {
        url: url.to_string(),
        timestamp: chrono::Utc::now().to_rfc3339(),
        metrics: Metrics {
            pages_scanned: 15,
            total_issues: 27,
            critical_issues: 5,
            warnings: 12,
            info: 10,
            health_score: 73,
        },
        issues: vec![
            Issue {
                severity: "critical".to_string(),
                category: "Meta Tags".to_string(),
                title: "Missing meta description".to_string(),
                description: "5 pages are missing meta descriptions which are crucial for SEO"
                    .to_string(),
                affected_pages: vec![
                    format!("{}/about", url),
                    format!("{}/contact", url),
                    format!("{}/services", url),
                ],
                recommendation: "Add unique meta descriptions to each page (150-160 characters)"
                    .to_string(),
            },
            Issue {
                severity: "critical".to_string(),
                category: "Links".to_string(),
                title: "Broken internal links".to_string(),
                description: "3 internal links are returning 404 errors".to_string(),
                affected_pages: vec![format!("{}/old-page", url)],
                recommendation: "Update or remove broken links to improve user experience"
                    .to_string(),
            },
            Issue {
                severity: "warning".to_string(),
                category: "Performance".to_string(),
                title: "Large unoptimized images".to_string(),
                description: "8 images are larger than 200KB and not optimized".to_string(),
                affected_pages: vec![format!("{}/gallery", url), format!("{}/products", url)],
                recommendation: "Compress images using WebP format or modern compression tools"
                    .to_string(),
            },
            Issue {
                severity: "warning".to_string(),
                category: "Security".to_string(),
                title: "Missing security headers".to_string(),
                description: "X-Content-Type-Options and X-Frame-Options headers are not set"
                    .to_string(),
                affected_pages: vec![url.to_string()],
                recommendation: "Add security headers to protect against XSS and clickjacking"
                    .to_string(),
            },
            Issue {
                severity: "info".to_string(),
                category: "Content".to_string(),
                title: "Short title tags".to_string(),
                description: "4 pages have title tags shorter than 30 characters".to_string(),
                affected_pages: vec![format!("{}/blog", url)],
                recommendation: "Expand title tags to 50-60 characters for better SEO impact"
                    .to_string(),
            },
        ],
        analysis: Some(
            "The website has a good foundation but needs attention to meta tags and performance optimization. Critical issues should be addressed first to improve search engine visibility and user experience."
                .to_string(),
        ),
    }
}
