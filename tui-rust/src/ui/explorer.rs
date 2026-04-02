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
        "Signal Explorer",
        "Visualize and analyze ECG waveforms",
    );

    let explorer = Paragraph::new(vec![
        Line::from("Signal Explorer - Coming Soon"),
        Line::from(""),
        Line::from("Features:"),
        Line::from("• View ECG waveforms with ASCII/Unicode charts"),
        Line::from("• Pan and zoom through signals"),
        Line::from("• Beat detection overlay"),
        Line::from("• Signal statistics"),
        Line::from("• Export to CSV"),
    ])
    .block(Block::default().borders(Borders::ALL).title("Explorer"))
    .alignment(Alignment::Left);

    frame.render_widget(explorer, content_area);

    render_footer(
        frame,
        footer_area,
        vec![("←→", "Pan"), ("+/-", "Zoom"), ("Esc", "Back")],
    );
}

pub fn handle_input(_app: &mut App, _key: KeyEvent) -> Result<()> {
    Ok(())
}
