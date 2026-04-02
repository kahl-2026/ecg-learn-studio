use crate::app::App;
use anyhow::Result;
use crossterm::event::KeyEvent;
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
        "Help",
        "Keyboard shortcuts and features",
    );

    let help = Paragraph::new(vec![
        Line::from(Span::styled(
            "Global Hotkeys",
            Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD),
        )),
        Line::from(""),
        Line::from("H - Go to Home screen"),
        Line::from("L - Learn ECG basics"),
        Line::from("E - Signal Explorer"),
        Line::from("T - Train models"),
        Line::from("P - Run predictions"),
        Line::from("Z - Quiz mode"),
        Line::from("? - Show this help"),
        Line::from("Esc - Back to Home (or close active subview)"),
        Line::from("Q - Quit application (outside active quiz question flow)"),
        Line::from(""),
        Line::from(Span::styled(
            "Features",
            Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD),
        )),
        Line::from(""),
        Line::from("• Interactive ECG lessons with beginner/intermediate modes"),
        Line::from("• Signal visualization with ASCII/Unicode charts"),
        Line::from("• Train Logistic Regression, Random Forest, and 1D CNN models"),
        Line::from("• Real-time training progress and metrics"),
        Line::from("• Prediction with confidence and plain-English explanations"),
        Line::from("• Quiz mode with 50+ questions across 6 categories"),
        Line::from("• Built-in glossary with 20+ ECG terms"),
        Line::from("• Colorblind-safe and monochrome themes"),
    ])
    .block(Block::default().borders(Borders::ALL).title("Help"))
    .alignment(Alignment::Left);

    frame.render_widget(help, content_area);

    render_footer(
        frame,
        footer_area,
        vec![("H", "Home"), ("Esc", "Back")],
    );
}

pub fn handle_input(_app: &mut App, _key: KeyEvent) -> Result<()> {
    Ok(())
}
