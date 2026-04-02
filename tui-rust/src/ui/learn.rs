use crate::app::{App, LessonContent};
use anyhow::Result;
use crossterm::event::{KeyCode, KeyEvent};
use ratatui::{
    layout::{Constraint, Direction, Layout, Alignment, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph, Wrap, List, ListItem, ListState},
    Frame,
};

use super::{create_layout, render_error_popup, render_footer, render_header, render_loading};

pub fn render(frame: &mut Frame, app: &App) {
    let (header_area, content_area, footer_area) = create_layout(frame);

    render_header(
        frame,
        header_area,
        "Learn ECG Basics",
        "Interactive lessons on ECG interpretation",
    );

    // Show loading indicator
    if app.learn_state.loading {
        render_loading(frame, content_area, "Loading lessons");
        render_footer(frame, footer_area, vec![("ESC", "Back")]);
        return;
    }

    // Show error if any
    if let Some(ref error) = app.learn_state.error {
        render_lesson_list(frame, app, content_area);
        render_error_popup(frame, error);
        render_footer(frame, footer_area, vec![("R", "Retry"), ("ESC", "Back")]);
        return;
    }

    if app.learn_state.viewing_content {
        // Render lesson content
        render_lesson_content(frame, app, content_area);
        render_footer(
            frame,
            footer_area,
            vec![
                ("B", if app.learn_state.beginner_mode { "Advanced" } else { "Beginner" }),
                ("↑/↓", "Scroll"),
                ("ESC", "Back to List"),
            ],
        );
    } else {
        // Render lesson list
        render_lesson_list(frame, app, content_area);
        render_footer(
            frame,
            footer_area,
            vec![
                ("↑/↓", "Navigate"),
                ("Enter", "Open"),
                ("B", if app.learn_state.beginner_mode { "Advanced" } else { "Beginner" }),
                ("1-7", "Jump"),
            ],
        );
    }
}

fn render_lesson_list(frame: &mut Frame, app: &App, area: Rect) {
    // Split into list and info panel
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(50), Constraint::Percentage(50)])
        .split(area);

    // Create lesson list items
    let items: Vec<ListItem> = if app.learn_state.lessons.is_empty() {
        // Show default lessons if none loaded from backend
        vec![
            create_lesson_item("1. What is an ECG?", "basics", 5, 0, app.learn_state.selected_index),
            create_lesson_item("2. The P Wave", "waves", 7, 1, app.learn_state.selected_index),
            create_lesson_item("3. The QRS Complex", "waves", 10, 2, app.learn_state.selected_index),
            create_lesson_item("4. The T Wave", "waves", 5, 3, app.learn_state.selected_index),
            create_lesson_item("5. PR Interval", "intervals", 6, 4, app.learn_state.selected_index),
            create_lesson_item("6. QT Interval", "intervals", 6, 5, app.learn_state.selected_index),
            create_lesson_item("7. Understanding Arrhythmias", "advanced", 15, 6, app.learn_state.selected_index),
        ]
    } else {
        app.learn_state.lessons.iter().enumerate().map(|(i, lesson)| {
            create_lesson_item(&lesson.title, &lesson.category, lesson.duration_minutes, i, app.learn_state.selected_index)
        }).collect()
    };

    let lessons_list = List::new(items)
        .block(Block::default().borders(Borders::ALL).title("Lessons"))
        .highlight_style(Style::default().bg(Color::DarkGray).add_modifier(Modifier::BOLD))
        .highlight_symbol("▶ ");

    let mut state = ListState::default();
    state.select(Some(app.learn_state.selected_index));
    frame.render_stateful_widget(lessons_list, chunks[0], &mut state);

    // Info panel
    let info_text = get_lesson_preview(app.learn_state.selected_index, app.learn_state.beginner_mode);
    let info = Paragraph::new(info_text)
        .block(Block::default().borders(Borders::ALL).title("Preview"))
        .wrap(Wrap { trim: true })
        .alignment(Alignment::Left);
    frame.render_widget(info, chunks[1]);
}

fn create_lesson_item(title: &str, category: &str, duration: u32, index: usize, selected: usize) -> ListItem<'static> {
    let style = if index == selected {
        Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)
    } else {
        Style::default().fg(Color::White)
    };

    let category_color = match category {
        "basics" => Color::Green,
        "waves" => Color::Blue,
        "intervals" => Color::Magenta,
        "advanced" => Color::Red,
        _ => Color::Gray,
    };

    ListItem::new(Line::from(vec![
        Span::styled(format!("{:<30}", title), style),
        Span::styled(format!(" [{:<10}]", category), Style::default().fg(category_color)),
        Span::styled(format!(" {} min", duration), Style::default().fg(Color::DarkGray)),
    ]))
}

fn get_lesson_preview(index: usize, beginner_mode: bool) -> Vec<Line<'static>> {
    let previews = if beginner_mode {
        vec![
            // Beginner mode previews
            vec![
                Line::from(Span::styled("What is an ECG?", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
                Line::from(""),
                Line::from("An ECG (electrocardiogram) is a simple test that records your heart's electrical activity."),
                Line::from(""),
                Line::from("Think of it like this: your heart is a pump that runs on electricity. Each heartbeat starts with a tiny electrical signal."),
                Line::from(""),
                Line::from(Span::styled("Key Points:", Style::default().fg(Color::Cyan))),
                Line::from("• Non-invasive and painless"),
                Line::from("• Shows heart rhythm and rate"),
                Line::from("• Helps detect heart problems"),
            ],
            vec![
                Line::from(Span::styled("The P Wave", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
                Line::from(""),
                Line::from("The P wave is the first bump you see in an ECG. It shows your atria (upper heart chambers) contracting."),
                Line::from(""),
                Line::from("Normal P wave: small, rounded, about 0.08-0.10 seconds wide."),
                Line::from(""),
                Line::from(Span::styled("Key Points:", Style::default().fg(Color::Cyan))),
                Line::from("• Represents atrial depolarization"),
                Line::from("• Should be upright in most leads"),
                Line::from("• Missing P waves may indicate AFib"),
            ],
            vec![
                Line::from(Span::styled("The QRS Complex", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
                Line::from(""),
                Line::from("The QRS complex is the tall spike in the ECG. It shows your ventricles (lower heart chambers) contracting."),
                Line::from(""),
                Line::from("Normal QRS: sharp and narrow, 0.06-0.10 seconds wide."),
                Line::from(""),
                Line::from(Span::styled("Key Points:", Style::default().fg(Color::Cyan))),
                Line::from("• Main pumping action of the heart"),
                Line::from("• Wide QRS may indicate problems"),
                Line::from("• R wave is the tall positive peak"),
            ],
            vec![
                Line::from(Span::styled("The T Wave", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
                Line::from(""),
                Line::from("The T wave comes after the QRS complex. It shows your ventricles resetting for the next beat."),
                Line::from(""),
                Line::from("Normal T wave: rounded, same direction as QRS."),
                Line::from(""),
                Line::from(Span::styled("Key Points:", Style::default().fg(Color::Cyan))),
                Line::from("• Represents ventricular repolarization"),
                Line::from("• Inverted T waves may indicate ischemia"),
                Line::from("• Tall T waves can indicate high potassium"),
            ],
            vec![
                Line::from(Span::styled("PR Interval", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
                Line::from(""),
                Line::from("The PR interval is the time from the start of the P wave to the start of the QRS complex."),
                Line::from(""),
                Line::from("Normal PR interval: 0.12-0.20 seconds."),
                Line::from(""),
                Line::from(Span::styled("Key Points:", Style::default().fg(Color::Cyan))),
                Line::from("• Shows AV node conduction time"),
                Line::from("• Long PR = first-degree heart block"),
                Line::from("• Short PR = pre-excitation syndrome"),
            ],
            vec![
                Line::from(Span::styled("QT Interval", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
                Line::from(""),
                Line::from("The QT interval measures total ventricular activity - from start of QRS to end of T wave."),
                Line::from(""),
                Line::from("Normal QT: varies with heart rate, usually < 0.44 seconds."),
                Line::from(""),
                Line::from(Span::styled("Key Points:", Style::default().fg(Color::Cyan))),
                Line::from("• Long QT can cause arrhythmias"),
                Line::from("• Must be corrected for heart rate (QTc)"),
                Line::from("• Some drugs prolong QT interval"),
            ],
            vec![
                Line::from(Span::styled("Understanding Arrhythmias", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
                Line::from(""),
                Line::from("Arrhythmias are abnormal heart rhythms. They can be too fast, too slow, or irregular."),
                Line::from(""),
                Line::from(Span::styled("Common Types:", Style::default().fg(Color::Cyan))),
                Line::from("• Normal Sinus Rhythm - healthy rhythm"),
                Line::from("• Atrial Fibrillation - irregular, no P waves"),
                Line::from("• Bradycardia - heart rate < 60 bpm"),
                Line::from("• Tachycardia - heart rate > 100 bpm"),
                Line::from("• PVC - extra beats from ventricles"),
            ],
        ]
    } else {
        // Advanced/intermediate mode previews
        vec![
            vec![
                Line::from(Span::styled("What is an ECG?", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
                Line::from(""),
                Line::from("The ECG records cardiac electrical potentials via surface electrodes, producing a voltage-time graph."),
                Line::from(""),
                Line::from("Standard 12-lead ECG provides 12 views: 6 limb leads (I, II, III, aVR, aVL, aVF) and 6 precordial leads (V1-V6)."),
                Line::from(""),
                Line::from(Span::styled("Technical Details:", Style::default().fg(Color::Cyan))),
                Line::from("• Standard paper speed: 25 mm/s"),
                Line::from("• Amplitude: 10 mm/mV"),
                Line::from("• Small box = 0.04s, large box = 0.20s"),
            ],
            vec![
                Line::from(Span::styled("The P Wave", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
                Line::from(""),
                Line::from("P wave represents sequential atrial depolarization, starting at the SA node."),
                Line::from(""),
                Line::from(Span::styled("Morphology:", Style::default().fg(Color::Cyan))),
                Line::from("• Duration: 80-100 ms"),
                Line::from("• Amplitude: < 2.5 mm"),
                Line::from("• Axis: 0° to +75°"),
                Line::from("• Biphasic in V1 (normal)"),
                Line::from(""),
                Line::from("P mitrale: notched P waves in left atrial enlargement"),
            ],
            vec![
                Line::from(Span::styled("The QRS Complex", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
                Line::from(""),
                Line::from("QRS represents ventricular depolarization. Septal activation (Q), apical (R), basal (S)."),
                Line::from(""),
                Line::from(Span::styled("Parameters:", Style::default().fg(Color::Cyan))),
                Line::from("• Duration: 60-100 ms (narrow)"),
                Line::from("• Wide QRS (>120ms): BBB, WPW, ventricular origin"),
                Line::from("• R wave progression: increases V1→V6"),
                Line::from("• Axis: -30° to +90° (normal)"),
            ],
            vec![
                Line::from(Span::styled("The T Wave", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
                Line::from(""),
                Line::from("T wave reflects ventricular repolarization. Direction usually follows QRS vector."),
                Line::from(""),
                Line::from(Span::styled("Clinical Significance:", Style::default().fg(Color::Cyan))),
                Line::from("• Inverted T: ischemia, strain, BBB"),
                Line::from("• Peaked T: hyperkalemia, early MI"),
                Line::from("• Flat T: hypokalemia, ischemia"),
                Line::from("• Biphasic T: ischemia, Wellens' syndrome"),
            ],
            vec![
                Line::from(Span::styled("PR Interval", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
                Line::from(""),
                Line::from("PR interval: SA node → AV node → Bundle of His conduction time."),
                Line::from(""),
                Line::from(Span::styled("Clinical Interpretation:", Style::default().fg(Color::Cyan))),
                Line::from("• Normal: 120-200 ms"),
                Line::from("• Long PR (>200ms): 1° AV block"),
                Line::from("• Short PR (<120ms): WPW, LGL syndrome"),
                Line::from("• Variable PR: 2° AV block Type I"),
            ],
            vec![
                Line::from(Span::styled("QT Interval", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
                Line::from(""),
                Line::from("QT measures total ventricular depolarization and repolarization. Rate-dependent."),
                Line::from(""),
                Line::from(Span::styled("QTc Formulas:", Style::default().fg(Color::Cyan))),
                Line::from("• Bazett: QTc = QT / √RR"),
                Line::from("• Fridericia: QTc = QT / ∛RR"),
                Line::from("• Long QT: QTc > 450ms (men), >460ms (women)"),
                Line::from("• Causes: drugs, electrolytes, congenital"),
            ],
            vec![
                Line::from(Span::styled("Understanding Arrhythmias", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
                Line::from(""),
                Line::from("Arrhythmias arise from abnormal automaticity, triggered activity, or re-entry circuits."),
                Line::from(""),
                Line::from(Span::styled("Classification:", Style::default().fg(Color::Cyan))),
                Line::from("• Supraventricular: AFib, AFlutter, SVT, MAT"),
                Line::from("• Ventricular: VT, VF, PVCs"),
                Line::from("• Conduction: AV blocks, BBB"),
                Line::from(""),
                Line::from("Key: analyze rate, rhythm, P waves, QRS morphology"),
            ],
        ]
    };

    previews.get(index).cloned().unwrap_or_else(|| vec![Line::from("Select a lesson to see preview")])
}

fn render_lesson_content(frame: &mut Frame, app: &App, area: Rect) {
    let content = if let Some(ref lesson) = app.learn_state.current_content {
        let mut lines = vec![
            Line::from(Span::styled(&lesson.title, Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))),
            Line::from(""),
        ];
        
        for paragraph in lesson.content.split('\n') {
            lines.push(Line::from(paragraph.to_string()));
        }
        
        if !lesson.key_points.is_empty() {
            lines.push(Line::from(""));
            lines.push(Line::from(Span::styled("Key Points:", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))));
            for point in &lesson.key_points {
                lines.push(Line::from(format!("• {}", point)));
            }
        }
        
        lines
    } else {
        // Use preview content when backend not connected
        get_lesson_preview(app.learn_state.selected_index, app.learn_state.beginner_mode)
    };

    let mode_label = if app.learn_state.beginner_mode { "Beginner" } else { "Advanced" };
    let content_widget = Paragraph::new(content)
        .block(Block::default().borders(Borders::ALL).title(format!("Lesson Content [{}]", mode_label)))
        .wrap(Wrap { trim: true })
        .alignment(Alignment::Left);
    frame.render_widget(content_widget, area);
}

pub fn handle_input(app: &mut App, key: KeyEvent) -> Result<()> {
    let max_lessons = if app.learn_state.lessons.is_empty() { 7 } else { app.learn_state.lessons.len() };

    match key.code {
        KeyCode::Up | KeyCode::Char('k') => {
            if !app.learn_state.viewing_content {
                if app.learn_state.selected_index > 0 {
                    app.learn_state.selected_index -= 1;
                }
            }
        }
        KeyCode::Down | KeyCode::Char('j') => {
            if !app.learn_state.viewing_content {
                if app.learn_state.selected_index < max_lessons - 1 {
                    app.learn_state.selected_index += 1;
                }
            }
        }
        KeyCode::Enter => {
            if !app.learn_state.viewing_content {
                // Try to load content from backend
                let lesson_ids = ["ecg_basics", "p_wave", "qrs_complex", "t_wave", "pr_interval", "qt_interval", "arrhythmias"];
                if let Some(lesson_id) = lesson_ids.get(app.learn_state.selected_index) {
                    let difficulty = if app.learn_state.beginner_mode { "beginner" } else { "intermediate" };
                    
                    match app.backend.request("get_lesson_content", serde_json::json!({
                        "lesson_id": lesson_id,
                        "difficulty": difficulty
                    })) {
                        Ok(response) => {
                            if let Some(result) = response.get("result") {
                                if let Ok(content) = serde_json::from_value::<LessonContent>(result.clone()) {
                                    app.learn_state.current_content = Some(content);
                                }
                            }
                        }
                        Err(_) => {
                            // Backend not available, use static content
                            app.learn_state.current_content = None;
                        }
                    }
                }
                app.learn_state.viewing_content = true;
            }
        }
        KeyCode::Esc => {
            if app.learn_state.viewing_content {
                app.learn_state.viewing_content = false;
                app.learn_state.current_content = None;
            }
        }
        KeyCode::Char('b') | KeyCode::Char('B') => {
            app.learn_state.beginner_mode = !app.learn_state.beginner_mode;
            // Reload content if viewing
            if app.learn_state.viewing_content {
                app.learn_state.current_content = None; // Will use static content
            }
        }
        KeyCode::Char('r') | KeyCode::Char('R') => {
            // Retry loading lessons
            if app.learn_state.error.is_some() {
                app.learn_state.error = None;
                app.learn_state.loading = true;
                // Load will happen on next update cycle
            }
        }
        KeyCode::Char(c @ '1'..='7') => {
            if !app.learn_state.viewing_content {
                let num = c.to_digit(10).unwrap_or(1) as usize;
                if num > 0 && num <= max_lessons {
                    app.learn_state.selected_index = num - 1;
                }
            }
        }
        _ => {}
    }
    Ok(())
}
