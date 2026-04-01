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
        "Quiz Mode",
        "Test your ECG knowledge",
    );

    let quiz = Paragraph::new(vec![
        Line::from(Span::styled(
            "ECG Knowledge Quiz",
            Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD),
        )),
        Line::from(""),
        Line::from("Select Category:"),
        Line::from(""),
        Line::from("1. ECG Basics"),
        Line::from("2. Wave Identification"),
        Line::from("3. Intervals and Measurements"),
        Line::from("4. Rhythm Recognition"),
        Line::from("5. Arrhythmias"),
        Line::from("6. ML Metrics Understanding"),
        Line::from(""),
        Line::from("Progress: 0/50 questions answered"),
        Line::from("Current streak: 0"),
    ])
    .block(Block::default().borders(Borders::ALL).title("Quiz"))
    .alignment(Alignment::Left);

    frame.render_widget(quiz, content_area);

    render_footer(
        frame,
        footer_area,
        vec![("1-6", "Select Category"), ("S", "Statistics"), ("Esc", "Back")],
    );
}

pub fn handle_input(_app: &mut App, _key: KeyEvent) -> Result<()> {
    Ok(())
}
