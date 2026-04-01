use crate::app::App;
use anyhow::Result;
use crossterm::event::{KeyCode, KeyEvent};
use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph},
    Frame,
};

use super::{create_layout, render_header, render_footer};

pub fn render(frame: &mut Frame, app: &App) {
    let (header_area, content_area, footer_area) = create_layout(frame);

    render_header(
        frame,
        header_area,
        "Home",
        "Welcome to ECG Learn Studio - Educational ECG Analysis Platform",
    );

    render_content(frame, content_area, app);

    render_footer(
        frame,
        footer_area,
        vec![
            ("H", "Home"),
            ("L", "Learn"),
            ("E", "Explorer"),
            ("T", "Train"),
            ("P", "Predict"),
            ("Z", "Quiz"),
            ("?", "Help"),
            ("Q", "Quit"),
        ],
    );
}

fn render_content(frame: &mut Frame, area: ratatui::layout::Rect, app: &App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(8),  // Banner
            Constraint::Length(10), // Menu
            Constraint::Min(0),     // Disclaimer
        ])
        .split(area);

    // ASCII Banner
    let banner = Paragraph::new(vec![
        Line::from("╔═══════════════════════════════════════════╗"),
        Line::from("║   ECG LEARN STUDIO                        ║"),
        Line::from("║   ▁▂▃▅▂▃▁ Educational Platform ▁▂▃▅▂▃▁    ║"),
        Line::from("╚═══════════════════════════════════════════╝"),
    ])
    .alignment(Alignment::Center)
    .style(Style::default().fg(Color::Cyan));

    frame.render_widget(banner, chunks[0]);

    // Navigation Menu
    let menu_items = vec![
        ("L", "Learn ECG Basics", "Step-by-step lessons on ECG interpretation"),
        ("E", "Signal Explorer", "Visualize and analyze ECG waveforms"),
        ("T", "Train Model", "Train ML models on ECG arrhythmias"),
        ("P", "Predict", "Run inference and get explanations"),
        ("Z", "Quiz Mode", "Test your ECG knowledge"),
        ("?", "Help", "Keyboard shortcuts and features"),
    ];

    let mut menu_lines = vec![
        Line::from(Span::styled(
            "Navigation",
            Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD),
        )),
        Line::from(""),
    ];

    for (key, title, desc) in menu_items {
        menu_lines.push(Line::from(vec![
            Span::styled(
                format!("[{}]", key),
                Style::default().fg(Color::Green).add_modifier(Modifier::BOLD),
            ),
            Span::raw(" "),
            Span::styled(title, Style::default().fg(Color::White).add_modifier(Modifier::BOLD)),
            Span::raw(" - "),
            Span::styled(desc, Style::default().fg(Color::Gray)),
        ]));
    }

    // Add backend status
    menu_lines.push(Line::from(""));
    let status_color = if app.backend_status.connected { Color::Green } else { Color::Red };
    menu_lines.push(Line::from(vec![
        Span::styled("Backend: ", Style::default().fg(Color::Gray)),
        Span::styled(
            &app.backend_status.message,
            Style::default().fg(status_color),
        ),
    ]));

    let menu = Paragraph::new(menu_lines)
        .block(Block::default().borders(Borders::ALL).title("Quick Start"))
        .alignment(Alignment::Left);

    frame.render_widget(menu, chunks[1]);

    // Disclaimer
    let disclaimer = Paragraph::new(vec![
        Line::from(""),
        Line::from(Span::styled(
            "⚠️  IMPORTANT: EDUCATIONAL USE ONLY ⚠️",
            Style::default().fg(Color::Red).add_modifier(Modifier::BOLD),
        )),
        Line::from(""),
        Line::from("This platform is designed for education and research purposes only."),
        Line::from("It is NOT intended for medical diagnosis or clinical decision-making."),
        Line::from("Do NOT use for emergency situations."),
        Line::from("Always consult qualified medical professionals for health concerns."),
    ])
    .block(Block::default().borders(Borders::ALL).title("Safety Notice"))
    .alignment(Alignment::Center)
    .style(Style::default().fg(Color::Yellow));

    frame.render_widget(disclaimer, chunks[2]);
}

pub fn handle_input(_app: &mut App, _key: KeyEvent) -> Result<()> {
    // Home screen doesn't need specific input handling
    // Navigation is handled globally
    Ok(())
}
