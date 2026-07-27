use ratatui::{
    backend::CrosstermBackend,
    layout::{Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, Paragraph},
    Terminal,
};
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use std::{
    io,
    time::{Duration, Instant},
    sync::{Arc, Mutex},
};

#[derive(Clone)]
pub struct Babylon60State {
    pub groups_monitored: usize,
    pub signals_detected: u64,
    pub snipes_executed: u64,
    pub pnl_eth: f64,
    pub log: Vec<String>,
    #[allow(dead_code)]
    pub active_ca: Option<String>,
}

impl Default for Babylon60State {
    fn default() -> Self {
        Self {
            groups_monitored: 0,
            signals_detected: 0,
            snipes_executed: 0,
            pnl_eth: 0.0,
            log: Vec::new(),
            active_ca: None,
        }
    }
}

pub fn run_dashboard(state: Arc<Mutex<Babylon60State>>) -> Result<(), io::Error> {
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let tick_rate = Duration::from_millis(250);
    let mut last_tick = Instant::now();

    loop {
        let s = state.lock().unwrap().clone();

        terminal.draw(|f| {
            let size = f.area();

            // Layout: Header + Main + Log
            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([
                    Constraint::Length(3),
                    Constraint::Length(8),
                    Constraint::Min(1),
                ])
                .split(size);

            // HEADER
            let header = Paragraph::new(Line::from(vec![
                Span::styled("▓▓ BABYLON60 OUROBOROS", Style::default()
                    .fg(Color::Rgb(0, 255, 100))
                    .add_modifier(Modifier::BOLD)),
                Span::raw("  |  "),
                Span::styled("AI DATA SNIPER v1.0", Style::default()
                    .fg(Color::Rgb(100, 100, 255))),
                Span::raw("  |  SOVEREIGN: MOSKV"),
            ]))
            .block(Block::default().borders(Borders::ALL)
                .border_style(Style::default().fg(Color::Rgb(30, 30, 30))));
            f.render_widget(header, chunks[0]);

            // METRICS
            let metrics_chunks = Layout::default()
                .direction(Direction::Horizontal)
                .constraints([
                    Constraint::Percentage(25),
                    Constraint::Percentage(25),
                    Constraint::Percentage(25),
                    Constraint::Percentage(25),
                ])
                .split(chunks[1]);

            let groups_w = Paragraph::new(format!("\n  {}", s.groups_monitored))
                .block(Block::default().borders(Borders::ALL).title(" GRUPOS ")
                    .border_style(Style::default().fg(Color::DarkGray)))
                .style(Style::default().fg(Color::White).add_modifier(Modifier::BOLD));
            f.render_widget(groups_w, metrics_chunks[0]);

            let signals_w = Paragraph::new(format!("\n  {}", s.signals_detected))
                .block(Block::default().borders(Borders::ALL).title(" SEÑALES ")
                    .border_style(Style::default().fg(Color::DarkGray)))
                .style(Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD));
            f.render_widget(signals_w, metrics_chunks[1]);

            let snipes_w = Paragraph::new(format!("\n  {}", s.snipes_executed))
                .block(Block::default().borders(Borders::ALL).title(" SNIPES ")
                    .border_style(Style::default().fg(Color::DarkGray)))
                .style(Style::default().fg(Color::Rgb(0, 255, 100)).add_modifier(Modifier::BOLD));
            f.render_widget(snipes_w, metrics_chunks[2]);

            let pnl_color = if s.pnl_eth >= 0.0 { Color::Rgb(0, 255, 100) } else { Color::Red };
            let pnl_w = Paragraph::new(format!("\n  {:.4} ETH", s.pnl_eth))
                .block(Block::default().borders(Borders::ALL).title(" PnL ")
                    .border_style(Style::default().fg(Color::DarkGray)))
                .style(Style::default().fg(pnl_color).add_modifier(Modifier::BOLD));
            f.render_widget(pnl_w, metrics_chunks[3]);

            // LOG STREAM
            let log_items: Vec<ListItem> = s.log.iter().rev().take(20)
                .map(|entry| {
                    let style = if entry.contains("SNIPE") {
                        Style::default().fg(Color::Rgb(0, 255, 100))
                    } else if entry.contains("ALERTA") || entry.contains("SCAM") {
                        Style::default().fg(Color::Red)
                    } else {
                        Style::default().fg(Color::DarkGray)
                    };
                    ListItem::new(entry.as_str()).style(style)
                })
                .collect();

            let log_widget = List::new(log_items)
                .block(Block::default().borders(Borders::ALL).title(" LOG STREAM (q: salir) ")
                    .border_style(Style::default().fg(Color::Rgb(30, 30, 30))));
            f.render_widget(log_widget, chunks[2]);
        })?;

        // Event handling
        let timeout = tick_rate
            .checked_sub(last_tick.elapsed())
            .unwrap_or_else(|| Duration::from_secs(0));

        if event::poll(timeout)? {
            if let Event::Key(key) = event::read()? {
                if key.code == KeyCode::Char('q') {
                    break;
                }
            }
        }

        if last_tick.elapsed() >= tick_rate {
            last_tick = Instant::now();
        }
    }

    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen, DisableMouseCapture)?;
    terminal.show_cursor()?;
    Ok(())
}
