use crate::app::App;
use anyhow::Result;
use crossterm::event::KeyEvent;
use ratatui::{
    layout::Alignment,
    text::Line,
    widgets::{Block, Borders, Paragraph},
    Frame,
};

use super::{create_layout, render_header, render_footer};

pub fn render(frame: &mut Frame, _app: &App) {
    let (header_area, content_area, footer_area) = create_layout(frame);

    render_header(
        frame,
        header_area,
        "Predict",
        "Run inference and get explanations",
    );

    let predict = Paragraph::new(vec![
        Line::from("Prediction Interface"),
        Line::from(""),
        Line::from("1. Select trained model"),
        Line::from("2. Load ECG signal"),
        Line::from("3. View prediction with confidence"),
        Line::from("4. Get plain-English explanation"),
    ])
    .block(Block::default().borders(Borders::ALL).title("Predict"))
    .alignment(Alignment::Left);

    frame.render_widget(predict, content_area);

    render_footer(
        frame,
        footer_area,
        vec![("Enter", "Predict"), ("E", "Explain"), ("Esc", "Back")],
    );
}

pub fn handle_input(_app: &mut App, _key: KeyEvent) -> Result<()> {
    Ok(())
}
