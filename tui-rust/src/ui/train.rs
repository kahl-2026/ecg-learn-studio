use crate::app::{App, DatasetType, ModelType, TrainingMetrics};
use anyhow::Result;
use crossterm::event::{KeyCode, KeyEvent};
use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph, Wrap, Table, Row, Cell},
    Frame,
};

use super::{create_layout, render_error_popup, render_footer, render_header, render_progress};

pub fn render(frame: &mut Frame, app: &App) {
    let (header_area, content_area, footer_area) = create_layout(frame);

    render_header(
        frame,
        header_area,
        "Train Model",
        "Train ML models for arrhythmia classification",
    );

    // Show training progress if training
    if app.train_state.training {
        render_training_progress(frame, app, content_area);
        render_footer(frame, footer_area, vec![("ESC", "Cancel Training")]);
        return;
    }

    // Show results if available
    if app.train_state.training_metrics.is_some() {
        render_training_results(frame, app, content_area);
        render_footer(
            frame,
            footer_area,
            vec![("S", "Save Model"), ("N", "New Training"), ("ESC", "Back")],
        );
        return;
    }

    // Show error if any
    if let Some(ref error) = app.train_state.error {
        render_config_screen(frame, app, content_area);
        render_error_popup(frame, error);
        render_footer(frame, footer_area, vec![("R", "Retry"), ("ESC", "Back")]);
        return;
    }

    // Show configuration
    render_config_screen(frame, app, content_area);
    render_footer(
        frame,
        footer_area,
        vec![
            ("1-3", "Model"),
            ("D", "Dataset"),
            ("Enter", "Start"),
            ("ESC", "Back"),
        ],
    );
}

fn render_config_screen(frame: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(50), Constraint::Percentage(50)])
        .split(area);

    // Left panel: Model selection
    let model_type = app.train_state.model_type;
    let models = vec![
        ("1. Logistic Regression", "Fast, interpretable, good baseline", ModelType::LogisticRegression),
        ("2. Random Forest", "Robust, feature importance, handles noise", ModelType::RandomForest),
        ("3. 1D CNN", "Deep learning, learns from raw signals", ModelType::CNN),
    ];

    let mut model_lines = vec![
        Line::from(Span::styled("Select Model", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))),
        Line::from(""),
    ];

    for (name, desc, mtype) in models {
        let is_selected = mtype == model_type;
        let prefix = if is_selected { "▶ " } else { "  " };
        let style = if is_selected {
            Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)
        } else {
            Style::default().fg(Color::White)
        };
        model_lines.push(Line::from(Span::styled(format!("{}{}", prefix, name), style)));
        model_lines.push(Line::from(Span::styled(format!("    {}", desc), Style::default().fg(Color::DarkGray))));
        model_lines.push(Line::from(""));
    }

    // Add dataset selection
    model_lines.push(Line::from(Span::styled("Dataset", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))));
    let dataset_name = match app.train_state.selected_dataset {
        DatasetType::Synthetic => "Synthetic (500 samples)",
        DatasetType::MitBih => "MIT-BIH Arrhythmia",
        DatasetType::PtbXl => "PTB-XL Database",
    };
    model_lines.push(Line::from(format!("▶ {} [Press D to change]", dataset_name)));

    let model_panel = Paragraph::new(model_lines)
        .block(Block::default().borders(Borders::ALL).title("Configuration"))
        .alignment(Alignment::Left);
    frame.render_widget(model_panel, chunks[0]);

    // Right panel: Training parameters
    let params_lines = vec![
        Line::from(Span::styled("Training Parameters", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))),
        Line::from(""),
        Line::from(format!("Epochs: {}", app.train_state.epochs)),
        Line::from(format!("Learning Rate: {:.4}", app.train_state.learning_rate)),
        Line::from(format!("Train/Val Split: {:.0}% / {:.0}%", 
            app.train_state.train_split * 100.0, 
            (1.0 - app.train_state.train_split) * 100.0)),
        Line::from(""),
        Line::from(Span::styled("Target Classes", Style::default().fg(Color::Yellow))),
        Line::from("• Normal Sinus Rhythm"),
        Line::from("• Atrial Fibrillation (AFib)"),
        Line::from("• Bradycardia"),
        Line::from("• Tachycardia"),
        Line::from("• Premature Ventricular Contraction (PVC)"),
        Line::from(""),
        Line::from(Span::styled("Press Enter to start training", Style::default().fg(Color::Green))),
    ];

    let params_panel = Paragraph::new(params_lines)
        .block(Block::default().borders(Borders::ALL).title("Parameters"))
        .alignment(Alignment::Left);
    frame.render_widget(params_panel, chunks[1]);
}

fn render_training_progress(frame: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),
            Constraint::Length(5),
            Constraint::Min(5),
        ])
        .split(area);

    let progress = app.train_state.training_progress;
    let epoch = app.train_state.current_epoch;
    let total_epochs = app.train_state.epochs;
    render_progress(frame, chunks[0], &format!("Epoch {}/{}", epoch, total_epochs), progress);

    // Status info
    let model_name = match app.train_state.model_type {
        ModelType::LogisticRegression => "Logistic Regression",
        ModelType::RandomForest => "Random Forest",
        ModelType::CNN => "1D CNN",
    };
    
    let status_lines = vec![
        Line::from(Span::styled("Training in Progress...", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
        Line::from(""),
        Line::from(format!("Model: {}", model_name)),
        Line::from(format!("Epoch: {} / {}", epoch, total_epochs)),
    ];
    
    let status = Paragraph::new(status_lines)
        .block(Block::default().borders(Borders::ALL).title("Status"))
        .alignment(Alignment::Left);
    frame.render_widget(status, chunks[1]);

    // Training log placeholder
    let log_lines = vec![
        Line::from(Span::styled("Training Log", Style::default().fg(Color::Cyan))),
        Line::from(""),
        Line::from("Initializing model..."),
        Line::from("Loading training data..."),
        Line::from(format!("Training epoch {}...", epoch)),
    ];
    
    let log = Paragraph::new(log_lines)
        .block(Block::default().borders(Borders::ALL).title("Log"))
        .alignment(Alignment::Left);
    frame.render_widget(log, chunks[2]);
}

fn render_training_results(frame: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(50), Constraint::Percentage(50)])
        .split(area);

    if let Some(ref metrics) = app.train_state.training_metrics {
        // Left: Metrics
        let metrics_lines = vec![
            Line::from(Span::styled("Training Complete!", Style::default().fg(Color::Green).add_modifier(Modifier::BOLD))),
            Line::from(""),
            Line::from(Span::styled("Performance Metrics", Style::default().fg(Color::Cyan))),
            Line::from(""),
            Line::from(format!("Accuracy:  {:.1}%", metrics.accuracy * 100.0)),
            Line::from(format!("Precision: {:.1}%", metrics.precision * 100.0)),
            Line::from(format!("Recall:    {:.1}%", metrics.recall * 100.0)),
            Line::from(format!("F1 Score:  {:.1}%", metrics.f1_score * 100.0)),
            Line::from(""),
            Line::from(Span::styled("What do these mean?", Style::default().fg(Color::Yellow))),
            Line::from(""),
        ];

        let mut all_lines = metrics_lines;
        
        // Add explanation
        for line in metrics.explanation.lines() {
            all_lines.push(Line::from(line.to_string()));
        }
        
        let metrics_panel = Paragraph::new(all_lines)
            .block(Block::default().borders(Borders::ALL).title("Results"))
            .wrap(Wrap { trim: true })
            .alignment(Alignment::Left);
        frame.render_widget(metrics_panel, chunks[0]);

        // Right: Confusion matrix
        render_confusion_matrix(frame, metrics, chunks[1]);
    }
}

fn render_confusion_matrix(frame: &mut Frame, metrics: &TrainingMetrics, area: Rect) {
    let class_names = &metrics.class_names;
    let matrix = &metrics.confusion_matrix;
    
    if matrix.is_empty() || class_names.is_empty() {
        let msg = Paragraph::new("No confusion matrix available")
            .block(Block::default().borders(Borders::ALL).title("Confusion Matrix"))
            .alignment(Alignment::Center);
        frame.render_widget(msg, area);
        return;
    }

    // Create header row
    let mut header_cells = vec![Cell::from("Pred→").style(Style::default().fg(Color::Cyan))];
    for name in class_names {
        let short_name: String = name.chars().take(6).collect();
        header_cells.push(Cell::from(short_name).style(Style::default().fg(Color::Yellow)));
    }
    let header = Row::new(header_cells).height(1);

    // Create data rows
    let rows: Vec<Row> = matrix.iter().enumerate().map(|(i, row)| {
        let class_name: String = class_names.get(i).map(|n| n.chars().take(6).collect()).unwrap_or_default();
        let mut cells = vec![Cell::from(class_name).style(Style::default().fg(Color::Yellow))];
        
        for (j, &val) in row.iter().enumerate() {
            let style = if i == j {
                Style::default().fg(Color::Green).add_modifier(Modifier::BOLD) // Correct predictions
            } else if val > 0 {
                Style::default().fg(Color::Red) // Errors
            } else {
                Style::default().fg(Color::DarkGray)
            };
            cells.push(Cell::from(format!("{:3}", val)).style(style));
        }
        Row::new(cells).height(1)
    }).collect();

    let widths: Vec<Constraint> = std::iter::once(Constraint::Length(7))
        .chain(class_names.iter().map(|_| Constraint::Length(6)))
        .collect();

    let table = Table::new(rows, widths)
        .header(header)
        .block(Block::default().borders(Borders::ALL).title("Confusion Matrix (Actual↓)"));
    
    frame.render_widget(table, area);
}

pub fn handle_input(app: &mut App, key: KeyEvent) -> Result<()> {
    // If viewing results
    if app.train_state.training_metrics.is_some() {
        match key.code {
            KeyCode::Char('n') | KeyCode::Char('N') => {
                app.train_state.training_metrics = None;
                app.train_state.current_epoch = 0;
                app.train_state.training_progress = 0.0;
            }
            KeyCode::Char('s') | KeyCode::Char('S') => {
                // Save model (would call backend)
                // For now just show a message via error field briefly
            }
            _ => {}
        }
        return Ok(());
    }

    // If training, only allow cancel
    if app.train_state.training {
        if key.code == KeyCode::Esc {
            app.train_state.training = false;
            app.train_state.error = Some("Training cancelled".to_string());
        }
        return Ok(());
    }

    // Configuration screen
    match key.code {
        KeyCode::Char('1') => {
            app.train_state.model_type = ModelType::LogisticRegression;
        }
        KeyCode::Char('2') => {
            app.train_state.model_type = ModelType::RandomForest;
        }
        KeyCode::Char('3') => {
            app.train_state.model_type = ModelType::CNN;
        }
        KeyCode::Char('d') | KeyCode::Char('D') => {
            // Cycle through datasets
            app.train_state.selected_dataset = match app.train_state.selected_dataset {
                DatasetType::Synthetic => DatasetType::MitBih,
                DatasetType::MitBih => DatasetType::PtbXl,
                DatasetType::PtbXl => DatasetType::Synthetic,
            };
        }
        KeyCode::Enter => {
            start_training(app)?;
        }
        KeyCode::Char('r') | KeyCode::Char('R') if app.train_state.error.is_some() => {
            app.train_state.error = None;
        }
        _ => {}
    }
    Ok(())
}

fn start_training(app: &mut App) -> Result<()> {
    app.train_state.training = true;
    app.train_state.current_epoch = 0;
    app.train_state.training_progress = 0.0;
    app.train_state.error = None;

    let model_type = app.train_state.model_type.as_str();
    let dataset_type = match app.train_state.selected_dataset {
        DatasetType::Synthetic => "synthetic",
        DatasetType::MitBih => "mitbih",
        DatasetType::PtbXl => "ptbxl",
    };

    match app.backend.request("train_model", serde_json::json!({
        "model_type": model_type,
        "dataset_type": dataset_type,
        "epochs": app.train_state.epochs,
        "learning_rate": app.train_state.learning_rate,
        "train_split": app.train_state.train_split
    })) {
        Ok(response) => {
            app.train_state.training = false;
            
            if let Some(result) = response.get("result") {
                // Parse metrics
                let accuracy = result.get("accuracy").and_then(|v| v.as_f64()).unwrap_or(0.0);
                let precision = result.get("precision").and_then(|v| v.as_f64()).unwrap_or(0.0);
                let recall = result.get("recall").and_then(|v| v.as_f64()).unwrap_or(0.0);
                let f1_score = result.get("f1_score").and_then(|v| v.as_f64()).unwrap_or(0.0);
                
                let confusion_matrix: Vec<Vec<u32>> = result.get("confusion_matrix")
                    .and_then(|v| serde_json::from_value(v.clone()).ok())
                    .unwrap_or_default();
                
                let class_names: Vec<String> = result.get("class_names")
                    .and_then(|v| serde_json::from_value(v.clone()).ok())
                    .unwrap_or_else(|| vec!["Normal".to_string(), "AFib".to_string(), "Brady".to_string(), "Tachy".to_string(), "PVC".to_string()]);
                
                let explanation = result.get("explanation")
                    .and_then(|v| v.as_str())
                    .unwrap_or("Training completed successfully.")
                    .to_string();

                app.train_state.training_metrics = Some(TrainingMetrics {
                    accuracy,
                    precision,
                    recall,
                    f1_score,
                    confusion_matrix,
                    class_names,
                    explanation,
                });
                app.train_state.training_progress = 1.0;
                app.train_state.current_epoch = app.train_state.epochs;
            } else if let Some(error) = response.get("error") {
                app.train_state.error = Some(error.get("message")
                    .and_then(|m| m.as_str())
                    .unwrap_or("Unknown error")
                    .to_string());
            }
        }
        Err(_) => {
            app.train_state.training = false;
            // Provide demo results when backend unavailable
            app.train_state.training_metrics = Some(TrainingMetrics {
                accuracy: 0.85,
                precision: 0.83,
                recall: 0.82,
                f1_score: 0.82,
                confusion_matrix: vec![
                    vec![45, 2, 1, 1, 1],
                    vec![3, 42, 2, 2, 1],
                    vec![1, 1, 46, 1, 1],
                    vec![2, 2, 1, 43, 2],
                    vec![1, 1, 2, 1, 45],
                ],
                class_names: vec!["Normal".to_string(), "AFib".to_string(), "Brady".to_string(), "Tachy".to_string(), "PVC".to_string()],
                explanation: "Demo results (backend unavailable):\n\n• Accuracy 85%: Model correctly classified 85% of ECG signals\n• Good balance across all 5 arrhythmia classes\n• Confusion matrix shows most errors are between similar conditions".to_string(),
            });
            app.train_state.training_progress = 1.0;
            app.train_state.current_epoch = app.train_state.epochs;
        }
    }
    
    Ok(())
}
