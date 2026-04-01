use crate::app::App;
use anyhow::Result;
use crossterm::event::{KeyCode, KeyEvent};
use ratatui::{
    layout::Alignment,
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph},
    Frame,
};

use super::{create_layout, render_header, render_footer};

pub fn render(frame: &mut Frame, _app: &App) {
    let (header_area, content_area, footer_area) = create_layout(frame);

    render_header(
        frame,
        header_area,
        "Learn ECG Basics",
        "Interactive lessons on ECG interpretation",
    );

    let lessons = Paragraph::new(vec![
        Line::from(Span::styled(
            "ECG Fundamentals",
            Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD),
        )),
        Line::from(""),
        Line::from("1. What is an ECG?"),
        Line::from("2. The P Wave - Atrial Activation"),
        Line::from("3. The QRS Complex - Ventricular Activation"),
        Line::from("4. The T Wave - Ventricular Repolarization"),
        Line::from("5. PR Interval - Conduction Time"),
        Line::from("6. QT Interval - Total Ventricular Activity"),
        Line::from("7. Understanding Arrhythmias"),
        Line::from(""),
        Line::from(Span::styled(
            "Press 1-7 to select a lesson",
            Style::default().fg(Color::Cyan),
        )),
    ])
    .block(Block::default().borders(Borders::ALL).title("Lessons"))
    .alignment(Alignment::Left);

    frame.render_widget(lessons, content_area);

    render_footer(
        frame,
        footer_area,
        vec![("1-7", "Select"), ("G", "Glossary"), ("Esc", "Back")],
    );
}

pub fn handle_input(_app: &mut App, _key: KeyEvent) -> Result<()> {
    Ok(())
}
