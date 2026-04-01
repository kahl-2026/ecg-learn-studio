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
        "Train Model",
        "Train ML models for arrhythmia classification",
    );

    let train = Paragraph::new(vec![
        Line::from(Span::styled(
            "Model Training",
            Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD),
        )),
        Line::from(""),
        Line::from("Select Model Type:"),
        Line::from(""),
        Line::from("1. Logistic Regression (Fast, interpretable)"),
        Line::from("2. Random Forest (Robust, feature importance)"),
        Line::from("3. 1D CNN (Deep learning, learns from raw signals)"),
        Line::from(""),
        Line::from("Dataset: Synthetic (500 samples, 5 classes)"),
        Line::from("Classes: Normal, AFib, Bradycardia, Tachycardia, PVC"),
    ])
    .block(Block::default().borders(Borders::ALL).title("Training"))
    .alignment(Alignment::Left);

    frame.render_widget(train, content_area);

    render_footer(
        frame,
        footer_area,
        vec![("1-3", "Select Model"), ("Enter", "Start Training"), ("Esc", "Back")],
    );
}

pub fn handle_input(_app: &mut App, _key: KeyEvent) -> Result<()> {
    Ok(())
}
