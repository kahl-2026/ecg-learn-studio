use crate::app::{App, QuizMode, QuizQuestion, QuizFeedback};
use anyhow::Result;
use crossterm::event::{KeyCode, KeyEvent};
use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Gauge, List, ListItem, ListState, Paragraph, Wrap},
    Frame,
};

use super::{create_layout, render_header, render_footer};

pub fn render(frame: &mut Frame, app: &App) {
    let (header_area, content_area, footer_area) = create_layout(frame);

    render_header(
        frame,
        header_area,
        "Quiz Mode",
        "Test your ECG knowledge",
    );

    // Show loading indicator
    if app.quiz_state.loading {
        let loading = Paragraph::new("Loading questions...")
            .style(Style::default().fg(Color::Yellow))
            .block(Block::default().borders(Borders::ALL).title("Quiz"))
            .alignment(Alignment::Center);
        frame.render_widget(loading, content_area);
        render_footer(frame, footer_area, vec![("ESC", "Back")]);
        return;
    }

    match app.quiz_state.mode {
        QuizMode::CategorySelect => {
            render_category_select(frame, app, content_area);
            render_footer(
                frame,
                footer_area,
                vec![("1-6", "Category"), ("↑/↓", "Navigate"), ("Enter", "Start"), ("S", "Stats")],
            );
        }
        QuizMode::Answering => {
            render_question(frame, app, content_area);
            render_footer(
                frame,
                footer_area,
                vec![("A-D", "Answer"), ("↑/↓", "Navigate"), ("Q", "Quit Quiz")],
            );
        }
        QuizMode::ShowingFeedback => {
            render_feedback(frame, app, content_area);
            render_footer(
                frame,
                footer_area,
                vec![("Enter/Space", "Next Question"), ("Q", "Quit Quiz")],
            );
        }
    }
}

fn render_category_select(frame: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(50), Constraint::Percentage(50)])
        .split(area);

    // Category list
    let items: Vec<ListItem> = app.quiz_state.categories.iter().enumerate().map(|(i, cat)| {
        let is_selected = i == app.quiz_state.selected_category_index;
        let style = if is_selected {
            Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)
        } else {
            Style::default().fg(Color::White)
        };

        let (correct, total) = app.quiz_state.category_stats
            .get(cat)
            .cloned()
            .unwrap_or((0, 0));
        
        let progress = if total > 0 {
            format!(" ({}/{})", correct, total)
        } else {
            String::new()
        };

        ListItem::new(Line::from(vec![
            Span::styled(format!("{}. ", i + 1), Style::default().fg(Color::Cyan)),
            Span::styled(cat.clone(), style),
            Span::styled(progress, Style::default().fg(Color::DarkGray)),
        ]))
    }).collect();

    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).title("Categories"))
        .highlight_style(Style::default().bg(Color::DarkGray))
        .highlight_symbol("▶ ");

    let mut state = ListState::default();
    state.select(Some(app.quiz_state.selected_category_index));
    frame.render_stateful_widget(list, chunks[0], &mut state);

    // Stats panel
    let accuracy = if app.quiz_state.total_answered > 0 {
        (app.quiz_state.score as f64 / app.quiz_state.total_answered as f64) * 100.0
    } else {
        0.0
    };

    let stats_lines = vec![
        Line::from(Span::styled("Quiz Statistics", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))),
        Line::from(""),
        Line::from(format!("Total Answered: {}", app.quiz_state.total_answered)),
        Line::from(format!("Correct: {}", app.quiz_state.score)),
        Line::from(format!("Accuracy: {:.1}%", accuracy)),
        Line::from(format!("Current Streak: {} 🔥", app.quiz_state.streak)),
        Line::from(""),
        Line::from(Span::styled("Category Progress:", Style::default().fg(Color::Yellow))),
        Line::from(""),
    ];

    let mut all_lines = stats_lines;
    for cat in &app.quiz_state.categories {
        let (correct, total) = app.quiz_state.category_stats.get(cat).cloned().unwrap_or((0, 0));
        let cat_accuracy = if total > 0 { (correct as f64 / total as f64) * 100.0 } else { 0.0 };
        let bar_width = (cat_accuracy / 5.0) as usize; // 20 chars = 100%
        let bar: String = "█".repeat(bar_width) + &"░".repeat(20 - bar_width);
        all_lines.push(Line::from(format!("{:<18} {} {:.0}%", cat, bar, cat_accuracy)));
    }

    let stats = Paragraph::new(all_lines)
        .block(Block::default().borders(Borders::ALL).title("Progress"))
        .wrap(Wrap { trim: true })
        .alignment(Alignment::Left);
    frame.render_widget(stats, chunks[1]);
}

fn render_question(frame: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),  // Progress bar
            Constraint::Min(10),    // Question
            Constraint::Length(6),  // Stats
        ])
        .split(area);

    // Progress bar
    let progress = if app.quiz_state.total_answered > 0 {
        app.quiz_state.score as f64 / app.quiz_state.total_answered as f64
    } else {
        0.0
    };
    
    let gauge = Gauge::default()
        .block(Block::default().borders(Borders::ALL).title(format!(
            "Score: {}/{} | Streak: {} 🔥",
            app.quiz_state.score, app.quiz_state.total_answered, app.quiz_state.streak
        )))
        .gauge_style(Style::default().fg(Color::Green).bg(Color::DarkGray))
        .percent((progress * 100.0) as u16)
        .label(format!("{:.1}% correct", progress * 100.0));
    frame.render_widget(gauge, chunks[0]);

    // Question and options
    if let Some(ref question) = app.quiz_state.current_question {
        let mut question_lines = vec![
            Line::from(Span::styled(
                format!("Category: {} | Difficulty: {}", question.category, question.difficulty),
                Style::default().fg(Color::DarkGray),
            )),
            Line::from(""),
            Line::from(Span::styled(&question.question, Style::default().fg(Color::White).add_modifier(Modifier::BOLD))),
            Line::from(""),
        ];

        let option_labels = ['A', 'B', 'C', 'D'];
        for (i, option) in question.options.iter().enumerate() {
            let is_selected = app.quiz_state.selected_answer == Some(i);
            let style = if is_selected {
                Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)
            } else {
                Style::default().fg(Color::White)
            };
            
            let prefix = if is_selected { "▶ " } else { "  " };
            question_lines.push(Line::from(vec![
                Span::styled(prefix, style),
                Span::styled(format!("{}. ", option_labels[i]), Style::default().fg(Color::Cyan)),
                Span::styled(option.clone(), style),
            ]));
        }

        question_lines.push(Line::from(""));
        question_lines.push(Line::from(Span::styled(
            "Press A, B, C, or D to select your answer",
            Style::default().fg(Color::Green),
        )));

        let question_widget = Paragraph::new(question_lines)
            .block(Block::default().borders(Borders::ALL).title("Question"))
            .wrap(Wrap { trim: true })
            .alignment(Alignment::Left);
        frame.render_widget(question_widget, chunks[1]);
    }

    // Hint
    let hint_lines = vec![
        Line::from(Span::styled("Tips:", Style::default().fg(Color::Cyan))),
        Line::from("• Use arrow keys or A-D to select"),
        Line::from("• Press Enter to confirm (optional)"),
        Line::from("• Press Q to quit the quiz"),
    ];
    let hints = Paragraph::new(hint_lines)
        .block(Block::default().borders(Borders::ALL).title("Help"))
        .alignment(Alignment::Left);
    frame.render_widget(hints, chunks[2]);
}

fn render_feedback(frame: &mut Frame, app: &App, area: Rect) {
    if let Some(ref feedback) = app.quiz_state.feedback {
        let (header_style, header_text) = if feedback.correct {
            (Style::default().fg(Color::Green).add_modifier(Modifier::BOLD), "✓ Correct!")
        } else {
            (Style::default().fg(Color::Red).add_modifier(Modifier::BOLD), "✗ Incorrect")
        };

        let mut lines = vec![
            Line::from(Span::styled(header_text, header_style)),
            Line::from(""),
        ];

        if !feedback.correct {
            lines.push(Line::from(vec![
                Span::raw("The correct answer was: "),
                Span::styled(&feedback.correct_answer, Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
            ]));
            lines.push(Line::from(""));
        }

        lines.push(Line::from(Span::styled("Explanation:", Style::default().fg(Color::Cyan))));
        lines.push(Line::from(""));
        
        for line in feedback.explanation.lines() {
            lines.push(Line::from(line.to_string()));
        }

        lines.push(Line::from(""));
        lines.push(Line::from(Span::styled(
            "Press Enter or Space for next question",
            Style::default().fg(Color::Green),
        )));

        // Add streak info
        if feedback.correct && app.quiz_state.streak > 1 {
            lines.push(Line::from(""));
            lines.push(Line::from(Span::styled(
                format!("🔥 {} answer streak!", app.quiz_state.streak),
                Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD),
            )));
        }

        let feedback_widget = Paragraph::new(lines)
            .block(Block::default().borders(Borders::ALL).title("Result"))
            .wrap(Wrap { trim: true })
            .alignment(Alignment::Left);
        frame.render_widget(feedback_widget, area);
    }
}

pub fn handle_input(app: &mut App, key: KeyEvent) -> Result<()> {
    match app.quiz_state.mode {
        QuizMode::CategorySelect => handle_category_select(app, key),
        QuizMode::Answering => handle_answering(app, key),
        QuizMode::ShowingFeedback => handle_feedback_input(app, key),
    }
}

fn handle_category_select(app: &mut App, key: KeyEvent) -> Result<()> {
    match key.code {
        KeyCode::Up | KeyCode::Char('k') => {
            if app.quiz_state.selected_category_index > 0 {
                app.quiz_state.selected_category_index -= 1;
            }
        }
        KeyCode::Down | KeyCode::Char('j') => {
            if app.quiz_state.selected_category_index < app.quiz_state.categories.len() - 1 {
                app.quiz_state.selected_category_index += 1;
            }
        }
        KeyCode::Char(c @ '1'..='6') => {
            let num = c.to_digit(10).unwrap_or(1) as usize;
            if num > 0 && num <= app.quiz_state.categories.len() {
                app.quiz_state.selected_category_index = num - 1;
            }
        }
        KeyCode::Enter => {
            // Start quiz for selected category
            load_question(app)?;
        }
        _ => {}
    }
    Ok(())
}

fn handle_answering(app: &mut App, key: KeyEvent) -> Result<()> {
    match key.code {
        KeyCode::Char('a') | KeyCode::Char('A') => {
            submit_answer(app, 0)?;
        }
        KeyCode::Char('b') | KeyCode::Char('B') => {
            submit_answer(app, 1)?;
        }
        KeyCode::Char('c') | KeyCode::Char('C') => {
            submit_answer(app, 2)?;
        }
        KeyCode::Char('d') | KeyCode::Char('D') => {
            submit_answer(app, 3)?;
        }
        KeyCode::Up | KeyCode::Char('k') => {
            if let Some(current) = app.quiz_state.selected_answer {
                if current > 0 {
                    app.quiz_state.selected_answer = Some(current - 1);
                }
            } else {
                app.quiz_state.selected_answer = Some(0);
            }
        }
        KeyCode::Down | KeyCode::Char('j') => {
            let max_options = app.quiz_state.current_question.as_ref().map(|q| q.options.len()).unwrap_or(4);
            if let Some(current) = app.quiz_state.selected_answer {
                if current < max_options - 1 {
                    app.quiz_state.selected_answer = Some(current + 1);
                }
            } else {
                app.quiz_state.selected_answer = Some(0);
            }
        }
        KeyCode::Enter => {
            if let Some(answer_idx) = app.quiz_state.selected_answer {
                submit_answer(app, answer_idx)?;
            }
        }
        KeyCode::Char('q') | KeyCode::Char('Q') => {
            app.quiz_state.mode = QuizMode::CategorySelect;
            app.quiz_state.current_question = None;
            app.quiz_state.selected_answer = None;
        }
        _ => {}
    }
    Ok(())
}

fn handle_feedback_input(app: &mut App, key: KeyEvent) -> Result<()> {
    match key.code {
        KeyCode::Enter | KeyCode::Char(' ') => {
            // Load next question
            app.quiz_state.feedback = None;
            load_question(app)?;
        }
        KeyCode::Char('q') | KeyCode::Char('Q') => {
            app.quiz_state.mode = QuizMode::CategorySelect;
            app.quiz_state.current_question = None;
            app.quiz_state.feedback = None;
            app.quiz_state.selected_answer = None;
        }
        _ => {}
    }
    Ok(())
}

fn load_question(app: &mut App) -> Result<()> {
    let category = app.quiz_state.categories
        .get(app.quiz_state.selected_category_index)
        .cloned()
        .unwrap_or_else(|| "ECG Basics".to_string());

    match app.backend.request("get_quiz_questions", serde_json::json!({
        "category": category,
        "count": 1
    })) {
        Ok(response) => {
            if let Some(result) = response.get("result") {
                if let Some(questions) = result.get("questions").and_then(|q| q.as_array()) {
                    if let Some(q) = questions.first() {
                        app.quiz_state.current_question = serde_json::from_value(q.clone()).ok();
                        app.quiz_state.mode = QuizMode::Answering;
                        app.quiz_state.selected_answer = None;
                        return Ok(());
                    }
                }
            }
        }
        Err(_) => {}
    }

    // Fallback to demo questions
    let demo_questions = get_demo_questions(&category);
    let idx = (app.quiz_state.total_answered as usize) % demo_questions.len();
    app.quiz_state.current_question = Some(demo_questions[idx].clone());
    app.quiz_state.mode = QuizMode::Answering;
    app.quiz_state.selected_answer = None;
    
    Ok(())
}

fn submit_answer(app: &mut App, answer_idx: usize) -> Result<()> {
    // Clone the question data we need before mutating app
    let question_data = app.quiz_state.current_question.as_ref().map(|q| {
        (q.id.clone(), q.options.get(answer_idx).cloned().unwrap_or_default(), q.category.clone(), q.clone())
    });
    
    if let Some((question_id, selected_answer, category, question)) = question_data {
        match app.backend.request("submit_quiz_answer", serde_json::json!({
            "question_id": question_id,
            "answer": selected_answer
        })) {
            Ok(response) => {
                if let Some(result) = response.get("result") {
                    let correct = result.get("correct").and_then(|v| v.as_bool()).unwrap_or(false);
                    let correct_answer = result.get("correct_answer")
                        .and_then(|v| v.as_str())
                        .unwrap_or("")
                        .to_string();
                    let explanation = result.get("explanation")
                        .and_then(|v| v.as_str())
                        .unwrap_or("")
                        .to_string();
                    
                    update_quiz_stats(app, &category, correct);
                    
                    app.quiz_state.feedback = Some(QuizFeedback {
                        correct,
                        correct_answer,
                        explanation,
                    });
                    app.quiz_state.mode = QuizMode::ShowingFeedback;
                    return Ok(());
                }
            }
            Err(_) => {}
        }

        // Fallback demo answer checking
        let (correct, correct_answer, explanation) = check_demo_answer(&question, answer_idx);
        update_quiz_stats(app, &category, correct);
        
        app.quiz_state.feedback = Some(QuizFeedback {
            correct,
            correct_answer,
            explanation,
        });
        app.quiz_state.mode = QuizMode::ShowingFeedback;
    }
    
    Ok(())
}

fn update_quiz_stats(app: &mut App, category: &str, correct: bool) {
    app.quiz_state.total_answered += 1;
    
    if correct {
        app.quiz_state.score += 1;
        app.quiz_state.streak += 1;
    } else {
        app.quiz_state.streak = 0;
    }
    
    let entry = app.quiz_state.category_stats.entry(category.to_string()).or_insert((0, 0));
    if correct {
        entry.0 += 1;
    }
    entry.1 += 1;
}

fn get_demo_questions(category: &str) -> Vec<QuizQuestion> {
    match category {
        "ECG Basics" => vec![
            QuizQuestion {
                id: "ecg-1".to_string(),
                question: "What does ECG stand for?".to_string(),
                options: vec![
                    "Electrocardiogram".to_string(),
                    "Electric Cardiac Graph".to_string(),
                    "Electro Cardiac Gram".to_string(),
                    "Electronic Cardio Guide".to_string(),
                ],
                category: "ECG Basics".to_string(),
                difficulty: "easy".to_string(),
            },
            QuizQuestion {
                id: "ecg-2".to_string(),
                question: "How many leads are in a standard ECG?".to_string(),
                options: vec![
                    "6 leads".to_string(),
                    "12 leads".to_string(),
                    "10 leads".to_string(),
                    "8 leads".to_string(),
                ],
                category: "ECG Basics".to_string(),
                difficulty: "easy".to_string(),
            },
        ],
        "Wave Identification" => vec![
            QuizQuestion {
                id: "wave-1".to_string(),
                question: "Which wave represents atrial depolarization?".to_string(),
                options: vec![
                    "P wave".to_string(),
                    "QRS complex".to_string(),
                    "T wave".to_string(),
                    "U wave".to_string(),
                ],
                category: "Wave Identification".to_string(),
                difficulty: "easy".to_string(),
            },
            QuizQuestion {
                id: "wave-2".to_string(),
                question: "What does the QRS complex represent?".to_string(),
                options: vec![
                    "Atrial repolarization".to_string(),
                    "Ventricular depolarization".to_string(),
                    "Ventricular repolarization".to_string(),
                    "Atrial depolarization".to_string(),
                ],
                category: "Wave Identification".to_string(),
                difficulty: "medium".to_string(),
            },
        ],
        "Arrhythmias" => vec![
            QuizQuestion {
                id: "arr-1".to_string(),
                question: "What is the hallmark of Atrial Fibrillation on ECG?".to_string(),
                options: vec![
                    "Irregularly irregular rhythm with absent P waves".to_string(),
                    "Regular rhythm with tall P waves".to_string(),
                    "Wide QRS complexes".to_string(),
                    "ST segment elevation".to_string(),
                ],
                category: "Arrhythmias".to_string(),
                difficulty: "medium".to_string(),
            },
            QuizQuestion {
                id: "arr-2".to_string(),
                question: "Bradycardia is defined as a heart rate below:".to_string(),
                options: vec![
                    "60 bpm".to_string(),
                    "50 bpm".to_string(),
                    "70 bpm".to_string(),
                    "80 bpm".to_string(),
                ],
                category: "Arrhythmias".to_string(),
                difficulty: "easy".to_string(),
            },
        ],
        _ => vec![
            QuizQuestion {
                id: "gen-1".to_string(),
                question: "What is the normal PR interval duration?".to_string(),
                options: vec![
                    "0.12-0.20 seconds".to_string(),
                    "0.06-0.10 seconds".to_string(),
                    "0.25-0.35 seconds".to_string(),
                    "0.40-0.50 seconds".to_string(),
                ],
                category: category.to_string(),
                difficulty: "medium".to_string(),
            },
        ],
    }
}

fn check_demo_answer(question: &QuizQuestion, answer_idx: usize) -> (bool, String, String) {
    // Demo answer key (first option is always correct in demo questions)
    let correct_idx = 0;
    let is_correct = answer_idx == correct_idx;
    let correct_answer = question.options.get(correct_idx).cloned().unwrap_or_default();
    
    let explanation = match question.id.as_str() {
        "ecg-1" => "ECG stands for Electrocardiogram, which is a recording of the heart's electrical activity.",
        "ecg-2" => "A standard 12-lead ECG uses 10 electrodes placed on the body to create 12 different views of the heart's electrical activity.",
        "wave-1" => "The P wave represents atrial depolarization - the electrical activity that causes the atria to contract.",
        "wave-2" => "The QRS complex represents ventricular depolarization - the electrical activity that causes the ventricles to contract, which is the main pumping action of the heart.",
        "arr-1" => "AFib is characterized by an irregularly irregular rhythm (no pattern to the irregularity) and absence of distinct P waves, replaced by fibrillatory waves.",
        "arr-2" => "Bradycardia is defined as a resting heart rate below 60 beats per minute. It may be normal in athletes or during sleep.",
        _ => "This is the correct answer based on standard ECG interpretation guidelines.",
    };
    
    (is_correct, correct_answer, explanation.to_string())
}
