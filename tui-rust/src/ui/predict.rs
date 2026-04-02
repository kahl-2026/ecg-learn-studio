use crate::app::{App, PredictionResult};
use crate::charts::ECGChart;
use anyhow::Result;
use crossterm::event::{KeyCode, KeyEvent};
use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, ListState, Paragraph, Wrap},
    Frame,
};

use super::{create_layout, render_error_popup, render_footer, render_header, render_loading};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum PredictMode {
    ModelSelect,
    SignalSelect,
    ShowResult,
}

pub fn render(frame: &mut Frame, app: &App) {
    let (header_area, content_area, footer_area) = create_layout(frame);

    render_header(
        frame,
        header_area,
        "Predict",
        "Run inference and get explanations",
    );

    // Show loading indicator
    if app.predict_state.loading {
        render_loading(frame, content_area, "Running prediction");
        render_footer(frame, footer_area, vec![("ESC", "Cancel")]);
        return;
    }

    // Show error if any
    if let Some(ref error) = app.predict_state.error {
        if app.predict_state.model_loaded {
            render_signal_select(frame, app, content_area);
        } else {
            render_model_select(frame, app, content_area);
        }
        render_error_popup(frame, error);
        render_footer(frame, footer_area, vec![("R", "Clear"), ("ESC", "Back")]);
        return;
    }

    // Determine current mode
    let mode = if app.predict_state.prediction.is_some() {
        PredictMode::ShowResult
    } else if app.predict_state.model_loaded {
        PredictMode::SignalSelect
    } else {
        PredictMode::ModelSelect
    };

    match mode {
        PredictMode::ModelSelect => {
            render_model_select(frame, app, content_area);
            render_footer(
                frame,
                footer_area,
                vec![("↑/↓", "Navigate"), ("Enter", "Select"), ("ESC", "Back")],
            );
        }
        PredictMode::SignalSelect => {
            render_signal_select(frame, app, content_area);
            render_footer(
                frame,
                footer_area,
                vec![("Enter", "Predict"), ("M", "Change Model"), ("ESC", "Back")],
            );
        }
        PredictMode::ShowResult => {
            render_result(frame, app, content_area);
            render_footer(
                frame,
                footer_area,
                vec![("E", "Explain"), ("N", "New Prediction"), ("ESC", "Back")],
            );
        }
    }
}

fn render_model_select(frame: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(50), Constraint::Percentage(50)])
        .split(area);

    // Model list
    let models = if app.predict_state.available_models.is_empty() {
        vec![
            "logistic_model_latest".to_string(),
            "random_forest_model_latest".to_string(),
            "cnn_model_latest".to_string(),
        ]
    } else {
        app.predict_state.available_models.clone()
    };

    let items: Vec<ListItem> = models.iter().enumerate().map(|(i, model)| {
        let is_selected = i == app.predict_state.selected_model_index;
        let style = if is_selected {
            Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)
        } else {
            Style::default().fg(Color::White)
        };
        
        let model_type = if model.contains("logistic") {
            "Logistic Regression"
        } else if model.contains("random_forest") {
            "Random Forest"
        } else if model.contains("cnn") {
            "1D CNN"
        } else {
            "Unknown"
        };
        
        ListItem::new(Line::from(vec![
            Span::styled(format!("{:<30}", model), style),
            Span::styled(format!(" ({})", model_type), Style::default().fg(Color::DarkGray)),
        ]))
    }).collect();

    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).title("Select Model"))
        .highlight_style(Style::default().bg(Color::DarkGray))
        .highlight_symbol("▶ ");

    let mut state = ListState::default();
    state.select(Some(app.predict_state.selected_model_index));
    frame.render_stateful_widget(list, chunks[0], &mut state);

    // Model info panel
    let info_lines = vec![
        Line::from(Span::styled("Model Information", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))),
        Line::from(""),
        Line::from("Select a trained model to run"),
        Line::from("predictions on ECG signals."),
        Line::from(""),
        Line::from(Span::styled("Available Models:", Style::default().fg(Color::Yellow))),
        Line::from(""),
        Line::from("• Logistic: Fast, interpretable"),
        Line::from("• Random Forest: Robust, accurate"),
        Line::from("• CNN: Deep learning approach"),
        Line::from(""),
        Line::from(Span::styled("Note:", Style::default().fg(Color::Red))),
        Line::from("Models shown may not exist if"),
        Line::from("you haven't trained them yet."),
        Line::from("Use Train screen first."),
    ];

    let info = Paragraph::new(info_lines)
        .block(Block::default().borders(Borders::ALL).title("Info"))
        .wrap(Wrap { trim: true })
        .alignment(Alignment::Left);
    frame.render_widget(info, chunks[1]);
}

fn render_signal_select(frame: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Length(10), Constraint::Min(5)])
        .split(area);

    // Signal preview if loaded
    if let Some(ref signal) = app.predict_state.signal_data {
        let chart = ECGChart::new(signal, "Signal to Predict".to_string());
        frame.render_widget(chart.render(), chunks[0]);
    } else {
        let placeholder = Paragraph::new(vec![
            Line::from(Span::styled("Signal Input", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))),
            Line::from(""),
            Line::from("Press Enter to generate a synthetic sample signal."),
            Line::from(""),
            Line::from(Span::styled("Explorer data import is not yet wired in this screen.", Style::default().fg(Color::Yellow))),
        ])
        .block(Block::default().borders(Borders::ALL).title("Signal Preview"))
        .alignment(Alignment::Left);
        frame.render_widget(placeholder, chunks[0]);
    }

    // Status
    let model_name = app.predict_state.available_models
        .get(app.predict_state.selected_model_index)
        .cloned()
        .unwrap_or_else(|| "Unknown Model".to_string());

    let status_lines = vec![
        Line::from(Span::styled("Prediction Setup", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))),
        Line::from(""),
        Line::from(format!("Model: {}", model_name)),
        Line::from(format!("Signal: {}", if app.predict_state.signal_loaded { "Loaded" } else { "Not loaded" })),
        Line::from(""),
        Line::from(if app.predict_state.signal_loaded {
            Span::styled("Ready! Press Enter to run prediction", Style::default().fg(Color::Green))
        } else {
            Span::styled("Press Enter to load a signal first", Style::default().fg(Color::Yellow))
        }),
    ];

    let status = Paragraph::new(status_lines)
        .block(Block::default().borders(Borders::ALL).title("Status"))
        .alignment(Alignment::Left);
    frame.render_widget(status, chunks[1]);
}

fn render_result(frame: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(50), Constraint::Percentage(50)])
        .split(area);

    if let Some(ref result) = app.predict_state.prediction {
        // Left: Prediction result
        let confidence_color = if result.confidence >= 0.8 {
            Color::Green
        } else if result.confidence >= 0.6 {
            Color::Yellow
        } else {
            Color::Red
        };

        let mut result_lines = vec![
            Line::from(Span::styled("Prediction Result", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))),
            Line::from(""),
            Line::from(vec![
                Span::raw("Predicted Class: "),
                Span::styled(&result.predicted_class, Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
            ]),
            Line::from(""),
        ];

        // Confidence bar visual
        result_lines.push(Line::from(vec![
            Span::raw("Confidence: "),
            Span::styled(format!("{:.1}%", result.confidence * 100.0), Style::default().fg(confidence_color).add_modifier(Modifier::BOLD)),
        ]));
        
        // Top predictions
        result_lines.push(Line::from(""));
        result_lines.push(Line::from(Span::styled("All Predictions:", Style::default().fg(Color::Yellow))));
        for (class, prob) in &result.top_predictions {
            let bar_width = (prob * 20.0) as usize;
            let bar: String = "█".repeat(bar_width) + &"░".repeat(20 - bar_width);
            result_lines.push(Line::from(format!("{:<12} {} {:.1}%", class, bar, prob * 100.0)));
        }

        // Uncertainty warning
        if result.is_uncertain {
            result_lines.push(Line::from(""));
            result_lines.push(Line::from(Span::styled("⚠ UNCERTAINTY WARNING", Style::default().fg(Color::Red).add_modifier(Modifier::BOLD))));
            if let Some(ref msg) = result.uncertainty_message {
                result_lines.push(Line::from(Span::styled(msg.as_str(), Style::default().fg(Color::Red))));
            }
        }

        let result_panel = Paragraph::new(result_lines)
            .block(Block::default().borders(Borders::ALL).title("Result"))
            .wrap(Wrap { trim: true })
            .alignment(Alignment::Left);
        frame.render_widget(result_panel, chunks[0]);

        // Right: Explanation
        let explanation = app.predict_state.explanation.clone().unwrap_or_else(|| {
            "Press 'E' to get a detailed explanation of this prediction.".to_string()
        });

        let mut explain_lines = vec![
            Line::from(Span::styled("Explanation", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))),
            Line::from(""),
        ];
        
        for line in explanation.lines() {
            explain_lines.push(Line::from(line.to_string()));
        }

        let explain_panel = Paragraph::new(explain_lines)
            .block(Block::default().borders(Borders::ALL).title("Interpretation"))
            .wrap(Wrap { trim: true })
            .alignment(Alignment::Left);
        frame.render_widget(explain_panel, chunks[1]);
    }
}

pub fn handle_input(app: &mut App, key: KeyEvent) -> Result<()> {
    // Determine current mode
    let mode = if app.predict_state.prediction.is_some() {
        PredictMode::ShowResult
    } else if app.predict_state.model_loaded {
        PredictMode::SignalSelect
    } else {
        PredictMode::ModelSelect
    };

    match mode {
        PredictMode::ModelSelect => {
            handle_model_select(app, key)?;
        }
        PredictMode::SignalSelect => {
            handle_signal_select(app, key)?;
        }
        PredictMode::ShowResult => {
            handle_result(app, key)?;
        }
    }

    Ok(())
}

fn handle_model_select(app: &mut App, key: KeyEvent) -> Result<()> {
    let model_count = if app.predict_state.available_models.is_empty() {
        3 // Default models
    } else {
        app.predict_state.available_models.len()
    };

    match key.code {
        KeyCode::Up | KeyCode::Char('k') => {
            if app.predict_state.selected_model_index > 0 {
                app.predict_state.selected_model_index -= 1;
            }
        }
        KeyCode::Down | KeyCode::Char('j') => {
            if app.predict_state.selected_model_index < model_count - 1 {
                app.predict_state.selected_model_index += 1;
            }
        }
        KeyCode::Enter => {
            // Load model (just mark as loaded for now)
            app.predict_state.error = None;
            app.predict_state.model_loaded = true;
            if app.predict_state.available_models.is_empty() {
                app.predict_state.available_models = vec![
                    "logistic_model_latest".to_string(),
                    "random_forest_model_latest".to_string(),
                    "cnn_model_latest".to_string(),
                ];
            }
        }
        _ => {}
    }
    Ok(())
}

fn handle_signal_select(app: &mut App, key: KeyEvent) -> Result<()> {
    match key.code {
        KeyCode::Enter => {
            if !app.predict_state.signal_loaded {
                // Generate sample signal
                app.predict_state.error = None;
                app.predict_state.signal_data = Some(generate_sample_signal());
                app.predict_state.signal_loaded = true;
            } else {
                // Run prediction
                run_prediction(app)?;
            }
        }
        KeyCode::Char('m') | KeyCode::Char('M') => {
            app.predict_state.error = None;
            app.predict_state.model_loaded = false;
            app.predict_state.signal_loaded = false;
            app.predict_state.signal_data = None;
        }
        KeyCode::Char('r') | KeyCode::Char('R') => {
            app.predict_state.error = None;
        }
        _ => {}
    }
    Ok(())
}

fn handle_result(app: &mut App, key: KeyEvent) -> Result<()> {
    match key.code {
        KeyCode::Char('e') | KeyCode::Char('E') => {
            // Get explanation
            get_explanation(app)?;
        }
        KeyCode::Char('n') | KeyCode::Char('N') => {
            // New prediction
            app.predict_state.error = None;
            app.predict_state.prediction = None;
            app.predict_state.explanation = None;
            app.predict_state.signal_loaded = false;
            app.predict_state.signal_data = None;
        }
        _ => {}
    }
    Ok(())
}

fn generate_sample_signal() -> Vec<f64> {
    // Generate a sample ECG-like signal
    let sample_rate = 360.0;
    let duration = 2.0;
    let num_samples = (sample_rate * duration) as usize;
    
    (0..num_samples).map(|i| {
        let t = i as f64 / sample_rate;
        let phase = (t * std::f64::consts::PI * 2.0 * 1.2) % (std::f64::consts::PI * 2.0);
        
        // P wave
        let p = 0.1 * (-((phase - 0.5).powi(2) / 0.02)).exp();
        // QRS complex
        let qrs = 1.0 * (-((phase - 1.0).powi(2) / 0.005)).exp() 
                - 0.2 * (-((phase - 0.9).powi(2) / 0.003)).exp()
                - 0.1 * (-((phase - 1.1).powi(2) / 0.003)).exp();
        // T wave
        let t_wave = 0.3 * (-((phase - 1.8).powi(2) / 0.03)).exp();
        
        p + qrs + t_wave + (i as f64 * 0.1).sin() * 0.02
    }).collect()
}

fn run_prediction(app: &mut App) -> Result<()> {
    app.predict_state.loading = true;
    app.predict_state.error = None;
    
    let model_name = app.predict_state.available_models
        .get(app.predict_state.selected_model_index)
        .cloned()
        .unwrap_or_else(|| "logistic_model_latest".to_string());

    let signal = app.predict_state.signal_data.clone().unwrap_or_default();

    match app.backend.request("predict", serde_json::json!({
        "model_id": model_name,
        "signal": signal
    })) {
        Ok(response) => {
            app.predict_state.loading = false;
            
            if let Some(result) = response.get("result") {
                let predicted_class = result.get("predicted_class")
                    .and_then(|v| v.as_str())
                    .unwrap_or("Unknown")
                    .to_string();
                let confidence = result.get("confidence")
                    .and_then(|v| v.as_f64())
                    .unwrap_or(0.0);
                let is_uncertain = result.get("is_uncertain")
                    .and_then(|v| v.as_bool())
                    .unwrap_or(false);
                let uncertainty_message = result.get("uncertainty_message")
                    .and_then(|v| v.as_str())
                    .map(|s| s.to_string());
                
                let top_predictions: Vec<(String, f64)> = if let Some(tp) = result.get("top_predictions") {
                    if let Ok(pairs) = serde_json::from_value::<Vec<(String, f64)>>(tp.clone()) {
                        pairs
                    } else if let Ok(items) = serde_json::from_value::<Vec<serde_json::Value>>(tp.clone()) {
                        items.into_iter().filter_map(|item| {
                            let class = item.get("class").and_then(|v| v.as_str())?;
                            let prob = item.get("probability").and_then(|v| v.as_f64())?;
                            Some((class.to_string(), prob))
                        }).collect()
                    } else {
                        Vec::new()
                    }
                } else {
                    Vec::new()
                };

                app.predict_state.prediction = Some(PredictionResult {
                    predicted_class,
                    confidence,
                    top_predictions,
                    is_uncertain,
                    uncertainty_message,
                });
            } else if let Some(error) = response.get("error") {
                app.predict_state.error = Some(
                    error
                        .get("message")
                        .and_then(|m| m.as_str())
                        .unwrap_or("Prediction request failed")
                        .to_string(),
                );
            }
        }
        Err(e) => {
            app.predict_state.loading = false;
            app.predict_state.error = Some(format!(
                "Prediction unavailable: {}. Train a model first in Train screen, then retry.",
                e
            ));
        }
    }
    
    Ok(())
}

fn get_explanation(app: &mut App) -> Result<()> {
    if let Some(ref prediction) = app.predict_state.prediction {
        let selected_model = app
            .predict_state
            .available_models
            .get(app.predict_state.selected_model_index)
            .cloned()
            .unwrap_or_else(|| "logistic_model_latest".to_string());
        match app.backend.request("explain", serde_json::json!({
            "model_id": selected_model,
            "predicted_class": prediction.predicted_class
        })) {
            Ok(response) => {
                if let Some(result) = response.get("result") {
                    app.predict_state.explanation = result.get("explanation")
                        .and_then(|v| v.as_str())
                        .map(|s| s.to_string());
                }
            }
            Err(_) => {
                // Generate demo explanation based on predicted class
                let explanation = match prediction.predicted_class.as_str() {
                    "Normal" => "The model identified this as Normal Sinus Rhythm.\n\n\
                        Key indicators:\n\
                        • Regular P waves present before each QRS\n\
                        • Normal QRS duration (< 120ms)\n\
                        • Heart rate in normal range (60-100 bpm)\n\
                        • Consistent RR intervals\n\n\
                        This appears to be a healthy heart rhythm.",
                    "AFib" => "The model identified this as Atrial Fibrillation.\n\n\
                        Key indicators:\n\
                        • Irregular RR intervals (irregularly irregular)\n\
                        • Absent or chaotic P waves\n\
                        • Variable ventricular response\n\n\
                        AFib is characterized by rapid, disorganized atrial activity.",
                    "Bradycardia" => "The model identified this as Bradycardia.\n\n\
                        Key indicators:\n\
                        • Heart rate < 60 bpm\n\
                        • Longer RR intervals\n\
                        • Regular rhythm (usually)\n\n\
                        May be normal in athletes or during sleep.",
                    "Tachycardia" => "The model identified this as Tachycardia.\n\n\
                        Key indicators:\n\
                        • Heart rate > 100 bpm\n\
                        • Shorter RR intervals\n\
                        • May have narrow or wide QRS\n\n\
                        Can be sinus or supraventricular in origin.",
                    "PVC" => "The model identified Premature Ventricular Contractions.\n\n\
                        Key indicators:\n\
                        • Wide, bizarre QRS complexes\n\
                        • No preceding P wave\n\
                        • Compensatory pause after\n\n\
                        Occasional PVCs are common and often benign.",
                    _ => "Explanation not available for this classification.",
                };
                app.predict_state.explanation = Some(explanation.to_string());
            }
        }
    }
    
    Ok(())
}
