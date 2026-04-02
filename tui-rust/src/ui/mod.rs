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
    widgets::{Block, Borders, Clear, Gauge, Paragraph, Wrap},
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

/// Render an error popup in the center of the screen
pub fn render_error_popup(frame: &mut Frame, error_message: &str) {
    let area = frame.size();
    let popup_width = (area.width * 60 / 100).min(60);
    let popup_height = 7.min(area.height.saturating_sub(4));
    let popup_area = centered_rect(popup_width, popup_height, area);
    
    // Clear the area behind the popup
    frame.render_widget(Clear, popup_area);
    
    // Create the error popup
    let error_block = Block::default()
        .title(" ⚠ Error ")
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Red))
        .style(Style::default().bg(Color::Black));
    
    let error_text = Paragraph::new(vec![
        Line::from(""),
        Line::from(Span::styled(
            error_message,
            Style::default().fg(Color::Red),
        )),
        Line::from(""),
        Line::from(Span::styled(
            "Press any key to dismiss",
            Style::default().fg(Color::Gray),
        )),
    ])
    .block(error_block)
    .alignment(Alignment::Center)
    .wrap(Wrap { trim: true });
    
    frame.render_widget(error_text, popup_area);
}

/// Render a loading indicator
pub fn render_loading(frame: &mut Frame, area: Rect, message: &str) {
    let loading_block = Block::default()
        .title(" Loading ")
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Cyan));
    
    // Animated loading dots (based on frame count, but we'll use static here)
    let dots = "...";
    
    let loading_text = Paragraph::new(vec![
        Line::from(""),
        Line::from(Span::styled(
            format!("{}{}", message, dots),
            Style::default().fg(Color::Yellow),
        )),
    ])
    .block(loading_block)
    .alignment(Alignment::Center);
    
    frame.render_widget(loading_text, area);
}

/// Render a progress bar with percentage
pub fn render_progress(frame: &mut Frame, area: Rect, label: &str, progress: f64) {
    let progress_clamped = progress.clamp(0.0, 1.0);
    let percentage = (progress_clamped * 100.0) as u16;
    
    let gauge = Gauge::default()
        .block(Block::default().title(label).borders(Borders::ALL))
        .gauge_style(
            Style::default()
                .fg(Color::Green)
                .bg(Color::DarkGray)
        )
        .ratio(progress_clamped)
        .label(format!("{}%", percentage));
    
    frame.render_widget(gauge, area);
}

/// Render a status message in the footer area
pub fn render_status(frame: &mut Frame, area: Rect, status: &str, status_type: StatusType) {
    let color = match status_type {
        StatusType::Info => Color::Cyan,
        StatusType::Success => Color::Green,
        StatusType::Warning => Color::Yellow,
        StatusType::Error => Color::Red,
    };
    
    let status_line = Line::from(Span::styled(
        status,
        Style::default().fg(color),
    ));
    
    let status_widget = Paragraph::new(status_line)
        .alignment(Alignment::Center);
    
    frame.render_widget(status_widget, area);
}

#[derive(Debug, Clone, Copy)]
pub enum StatusType {
    Info,
    Success,
    Warning,
    Error,
}

/// Center a rectangle within another rectangle
pub fn centered_rect(width: u16, height: u16, area: Rect) -> Rect {
    let x = area.x + (area.width.saturating_sub(width)) / 2;
    let y = area.y + (area.height.saturating_sub(height)) / 2;
    Rect::new(x, y, width.min(area.width), height.min(area.height))
}
