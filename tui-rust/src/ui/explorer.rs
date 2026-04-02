use crate::app::{App, DatasetType, SignalData};
use crate::charts::ECGChart;
use anyhow::Result;
use crossterm::event::{KeyCode, KeyEvent};
use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph, Wrap},
    Frame,
};

use super::{create_layout, render_error_popup, render_footer, render_header, render_loading};

pub fn render(frame: &mut Frame, app: &App) {
    let (header_area, content_area, footer_area) = create_layout(frame);

    render_header(
        frame,
        header_area,
        "Signal Explorer",
        "Visualize and analyze ECG waveforms",
    );

    // Show loading indicator
    if app.explorer_state.loading {
        render_loading(frame, content_area, "Loading signal data");
        render_footer(frame, footer_area, vec![("ESC", "Back")]);
        return;
    }

    // Show error if any
    if let Some(ref error) = app.explorer_state.error {
        render_dataset_selector(frame, app, content_area);
        render_error_popup(frame, error);
        render_footer(frame, footer_area, vec![("R", "Retry"), ("ESC", "Back")]);
        return;
    }

    // Split content area: chart (main) + stats (side panel)
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(70), Constraint::Percentage(30)])
        .split(content_area);

    // Render ECG chart or dataset selector
    if app.explorer_state.signal_data.is_some() {
        render_chart(frame, app, chunks[0]);
    } else {
        render_dataset_selector(frame, app, chunks[0]);
    }

    // Render stats/info panel
    render_stats_panel(frame, app, chunks[1]);

    // Footer with context-appropriate controls
    if app.explorer_state.signal_data.is_some() {
        render_footer(
            frame,
            footer_area,
            vec![
                ("←/→", "Scroll"),
                ("+/-", "Zoom"),
                ("↑/↓", "Signal"),
                ("N", "New Dataset"),
                ("ESC", "Back"),
            ],
        );
    } else {
        render_footer(
            frame,
            footer_area,
            vec![
                ("1", "Synthetic"),
                ("2", "MIT-BIH"),
                ("3", "PTB-XL"),
                ("Enter", "Load"),
                ("ESC", "Back"),
            ],
        );
    }
}

fn render_dataset_selector(frame: &mut Frame, app: &App, area: Rect) {
    let dataset_type = app.explorer_state.dataset_type;
    
    let items = vec![
        ("1. Synthetic ECG", "Generated ECG samples with 5 arrhythmia types", DatasetType::Synthetic),
        ("2. MIT-BIH Database", "Real arrhythmia annotations (requires download)", DatasetType::MitBih),
        ("3. PTB-XL Database", "Large ECG dataset (requires download)", DatasetType::PtbXl),
    ];

    let lines: Vec<Line> = items.iter().map(|(name, desc, dtype)| {
        let is_selected = *dtype == dataset_type;
        let prefix = if is_selected { "▶ " } else { "  " };
        let style = if is_selected {
            Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)
        } else {
            Style::default().fg(Color::White)
        };
        Line::from(vec![
            Span::styled(prefix, style),
            Span::styled(*name, style),
            Span::styled(format!(" - {}", desc), Style::default().fg(Color::DarkGray)),
        ])
    }).collect();

    let mut all_lines = vec![
        Line::from(Span::styled("Select Dataset", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))),
        Line::from(""),
    ];
    all_lines.extend(lines);
    all_lines.push(Line::from(""));
    all_lines.push(Line::from(Span::styled(
        "Press Enter to load selected dataset",
        Style::default().fg(Color::Green),
    )));

    let selector = Paragraph::new(all_lines)
        .block(Block::default().borders(Borders::ALL).title("Dataset Selection"))
        .alignment(Alignment::Left);
    frame.render_widget(selector, area);
}

fn render_chart(frame: &mut Frame, app: &App, area: Rect) {
    if let Some(ref data) = app.explorer_state.signal_data {
        let signal_idx = app.explorer_state.selected_signal_index;
        if signal_idx < data.signals.len() {
            let signal = &data.signals[signal_idx];
            let label = data.labels.get(signal_idx).cloned().unwrap_or_else(|| "Unknown".to_string());
            
            // Apply viewport and zoom
            let viewport_start = app.explorer_state.viewport_start;
            let zoom = app.explorer_state.zoom_level;
            let window_size = ((area.width as f64 * 2.0) / zoom) as usize; // 2 samples per char approx
            let window_size = window_size.max(50).min(signal.len());
            
            let start = viewport_start.min(signal.len().saturating_sub(window_size));
            let end = (start + window_size).min(signal.len());
            let visible_signal: Vec<f64> = signal[start..end].to_vec();
            
            let title = format!("Signal {} - {} (samples {}-{})", signal_idx + 1, label, start, end);
            let chart = ECGChart::new(&visible_signal, title);
            frame.render_widget(chart.render(), area);
        } else {
            let msg = Paragraph::new("No signal data available")
                .block(Block::default().borders(Borders::ALL).title("Chart"))
                .alignment(Alignment::Center);
            frame.render_widget(msg, area);
        }
    }
}

fn render_stats_panel(frame: &mut Frame, app: &App, area: Rect) {
    let mut lines = vec![
        Line::from(Span::styled("Signal Information", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))),
        Line::from(""),
    ];

    if let Some(ref data) = app.explorer_state.signal_data {
        let signal_idx = app.explorer_state.selected_signal_index;
        
        // Dataset info
        let dataset_name = match app.explorer_state.dataset_type {
            DatasetType::Synthetic => "Synthetic",
            DatasetType::MitBih => "MIT-BIH",
            DatasetType::PtbXl => "PTB-XL",
        };
        lines.push(Line::from(format!("Dataset: {}", dataset_name)));
        lines.push(Line::from(format!("Signals: {}", data.signals.len())));
        lines.push(Line::from(format!("Sample Rate: {} Hz", data.sample_rate)));
        lines.push(Line::from(""));
        
        // Current signal info
        if signal_idx < data.signals.len() {
            let signal = &data.signals[signal_idx];
            let label = data.labels.get(signal_idx).cloned().unwrap_or_else(|| "Unknown".to_string());
            
            lines.push(Line::from(Span::styled("Current Signal", Style::default().fg(Color::Yellow))));
            lines.push(Line::from(format!("Index: {} / {}", signal_idx + 1, data.signals.len())));
            lines.push(Line::from(format!("Label: {}", label)));
            lines.push(Line::from(format!("Samples: {}", signal.len())));
            
            // Calculate stats
            let min_val = signal.iter().cloned().fold(f64::INFINITY, f64::min);
            let max_val = signal.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
            let mean_val: f64 = signal.iter().sum::<f64>() / signal.len() as f64;
            let duration_sec = signal.len() as f64 / data.sample_rate;
            
            lines.push(Line::from(""));
            lines.push(Line::from(Span::styled("Statistics", Style::default().fg(Color::Yellow))));
            lines.push(Line::from(format!("Duration: {:.2}s", duration_sec)));
            lines.push(Line::from(format!("Min: {:.4}", min_val)));
            lines.push(Line::from(format!("Max: {:.4}", max_val)));
            lines.push(Line::from(format!("Mean: {:.4}", mean_val)));
            
            // Zoom info
            lines.push(Line::from(""));
            lines.push(Line::from(Span::styled("View", Style::default().fg(Color::Yellow))));
            lines.push(Line::from(format!("Zoom: {:.1}x", app.explorer_state.zoom_level)));
            lines.push(Line::from(format!("Position: {}", app.explorer_state.viewport_start)));
        }
    } else {
        lines.push(Line::from("No data loaded"));
        lines.push(Line::from(""));
        lines.push(Line::from("Select a dataset and press"));
        lines.push(Line::from("Enter to load signal data."));
        lines.push(Line::from(""));
        lines.push(Line::from(Span::styled("Tip:", Style::default().fg(Color::Green))));
        lines.push(Line::from("Synthetic data is always"));
        lines.push(Line::from("available without download."));
    }

    let stats = Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL).title("Info"))
        .wrap(Wrap { trim: true })
        .alignment(Alignment::Left);
    frame.render_widget(stats, area);
}

pub fn handle_input(app: &mut App, key: KeyEvent) -> Result<()> {
    match key.code {
        // Dataset selection
        KeyCode::Char('1') if app.explorer_state.signal_data.is_none() => {
            app.explorer_state.dataset_type = DatasetType::Synthetic;
        }
        KeyCode::Char('2') if app.explorer_state.signal_data.is_none() => {
            app.explorer_state.dataset_type = DatasetType::MitBih;
        }
        KeyCode::Char('3') if app.explorer_state.signal_data.is_none() => {
            app.explorer_state.dataset_type = DatasetType::PtbXl;
        }
        
        // Load dataset
        KeyCode::Enter if app.explorer_state.signal_data.is_none() => {
            load_dataset(app)?;
        }
        
        // Navigation when data loaded
        KeyCode::Left if app.explorer_state.signal_data.is_some() => {
            let scroll_amount = 50;
            app.explorer_state.viewport_start = app.explorer_state.viewport_start.saturating_sub(scroll_amount);
        }
        KeyCode::Right if app.explorer_state.signal_data.is_some() => {
            if let Some(ref data) = app.explorer_state.signal_data {
                let signal_idx = app.explorer_state.selected_signal_index;
                if signal_idx < data.signals.len() {
                    let max_pos = data.signals[signal_idx].len().saturating_sub(100);
                    app.explorer_state.viewport_start = (app.explorer_state.viewport_start + 50).min(max_pos);
                }
            }
        }
        
        // Signal navigation
        KeyCode::Up if app.explorer_state.signal_data.is_some() => {
            if app.explorer_state.selected_signal_index > 0 {
                app.explorer_state.selected_signal_index -= 1;
                app.explorer_state.viewport_start = 0; // Reset view for new signal
            }
        }
        KeyCode::Down if app.explorer_state.signal_data.is_some() => {
            if let Some(ref data) = app.explorer_state.signal_data {
                if app.explorer_state.selected_signal_index < data.signals.len() - 1 {
                    app.explorer_state.selected_signal_index += 1;
                    app.explorer_state.viewport_start = 0;
                }
            }
        }
        
        // Zoom
        KeyCode::Char('+') | KeyCode::Char('=') => {
            app.explorer_state.zoom_level = (app.explorer_state.zoom_level * 1.5).min(10.0);
        }
        KeyCode::Char('-') | KeyCode::Char('_') => {
            app.explorer_state.zoom_level = (app.explorer_state.zoom_level / 1.5).max(0.1);
        }
        
        // New dataset
        KeyCode::Char('n') | KeyCode::Char('N') => {
            app.explorer_state.signal_data = None;
            app.explorer_state.viewport_start = 0;
            app.explorer_state.selected_signal_index = 0;
            app.explorer_state.zoom_level = 1.0;
        }
        
        // Retry on error
        KeyCode::Char('r') | KeyCode::Char('R') if app.explorer_state.error.is_some() => {
            app.explorer_state.error = None;
            load_dataset(app)?;
        }
        
        _ => {}
    }
    Ok(())
}

fn load_dataset(app: &mut App) -> Result<()> {
    app.explorer_state.loading = true;
    app.explorer_state.error = None;
    
    let dataset_type = match app.explorer_state.dataset_type {
        DatasetType::Synthetic => "synthetic",
        DatasetType::MitBih => "mitbih",
        DatasetType::PtbXl => "ptbxl",
    };

    match app.backend.request("load_data", serde_json::json!({
        "dataset_type": dataset_type,
        "count": 40
    })) {
        Ok(response) => {
            app.explorer_state.loading = false;
            if let Some(result) = response.get("result") {
                // Parse response
                let signals: Vec<Vec<f64>> = result.get("signals")
                    .and_then(|s| serde_json::from_value(s.clone()).ok())
                    .unwrap_or_default();
                let labels: Vec<String> = result.get("labels")
                    .and_then(|l| serde_json::from_value(l.clone()).ok())
                    .unwrap_or_default();
                let sample_rate: f64 = result.get("sample_rate")
                    .and_then(|r| r.as_f64())
                    .unwrap_or(360.0);
                
                if signals.is_empty() {
                    app.explorer_state.error = Some("No signals returned from backend".to_string());
                } else {
                    app.explorer_state.signal_data = Some(SignalData {
                        total_samples: signals.iter().map(|s| s.len()).sum(),
                        signals,
                        labels,
                        sample_rate,
                    });
                }
            } else if let Some(error) = response.get("error") {
                app.explorer_state.error = Some(error.get("message")
                    .and_then(|m| m.as_str())
                    .unwrap_or("Unknown error")
                    .to_string());
            }
        }
        Err(_) => {
            app.explorer_state.loading = false;
            // Generate synthetic data locally as fallback
            app.explorer_state.signal_data = Some(generate_demo_signals());
        }
    }
    
    Ok(())
}

fn generate_demo_signals() -> SignalData {
    // Generate simple synthetic ECG-like signals for demo when backend unavailable
    let mut signals = Vec::new();
    let mut labels = Vec::new();
    let sample_rate = 360.0;
    
    let classes = ["Normal", "AFib", "Bradycardia", "Tachycardia", "PVC"];
    
    for (i, class) in classes.iter().enumerate() {
        let mut signal = Vec::with_capacity(720); // 2 seconds at 360 Hz
        
        for j in 0..720 {
            let t = j as f64 / sample_rate;
            // Simple ECG-like waveform
            let phase = (t * std::f64::consts::PI * 2.0 * (1.0 + i as f64 * 0.3)) % (std::f64::consts::PI * 2.0);
            
            // P wave
            let p = 0.1 * (-((phase - 0.5).powi(2) / 0.02)).exp();
            // QRS complex
            let qrs = 1.0 * (-((phase - 1.0).powi(2) / 0.005)).exp() 
                    - 0.2 * (-((phase - 0.9).powi(2) / 0.003)).exp()
                    - 0.1 * (-((phase - 1.1).powi(2) / 0.003)).exp();
            // T wave
            let t_wave = 0.3 * (-((phase - 1.8).powi(2) / 0.03)).exp();
            
            // Add noise
            let noise = (j as f64 * 0.1).sin() * 0.02;
            
            signal.push(p + qrs + t_wave + noise);
        }
        
        signals.push(signal);
        labels.push(class.to_string());
    }
    
    SignalData {
        signals,
        labels,
        sample_rate,
        total_samples: 720 * 5,
    }
}
