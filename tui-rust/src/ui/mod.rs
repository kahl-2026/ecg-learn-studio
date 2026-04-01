pub mod home;
pub mod learn;
pub mod explorer;
pub mod train;
pub mod predict;
pub mod quiz;
pub mod help;

use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph},
    Frame,
};

pub fn create_layout(frame: &Frame) -> (Rect, Rect, Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),  // Header
            Constraint::Min(0),     // Content
            Constraint::Length(3),  // Footer with hotkeys
        ])
        .split(frame.size());

    (chunks[0], chunks[1], chunks[2])
}

pub fn render_header(frame: &mut Frame, area: Rect, title: &str, subtitle: &str) {
    let header = Paragraph::new(vec![
        Line::from(vec![
            Span::styled(
                "ECG Learn Studio",
                Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD),
            ),
            Span::raw(" | "),
            Span::styled(title, Style::default().fg(Color::Yellow)),
        ]),
        Line::from(Span::styled(
            subtitle,
            Style::default().fg(Color::Gray),
        )),
    ])
    .block(Block::default().borders(Borders::BOTTOM))
    .alignment(Alignment::Left);

    frame.render_widget(header, area);
}

pub fn render_footer(frame: &mut Frame, area: Rect, hotkeys: Vec<(&str, &str)>) {
    let mut spans = vec![];
    for (i, (key, desc)) in hotkeys.iter().enumerate() {
        if i > 0 {
            spans.push(Span::raw(" | "));
        }
        spans.push(Span::styled(
            *key,
            Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD),
        ));
        spans.push(Span::raw(": "));
        spans.push(Span::raw(*desc));
    }

    let footer = Paragraph::new(Line::from(spans))
        .block(Block::default().borders(Borders::TOP))
        .alignment(Alignment::Center);

    frame.render_widget(footer, area);
}
