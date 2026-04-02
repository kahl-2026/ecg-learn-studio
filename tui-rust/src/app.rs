use anyhow::Result;
use crossterm::event::{KeyCode, KeyEvent};
use ratatui::Frame;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use crate::backend::PythonBackend;
use crate::config::Config;
use crate::ui::{home, learn, explorer, train, predict, quiz, help};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Screen {
    Home,
    Learn,
    Explorer,
    Train,
    Predict,
    Quiz,
    Help,
}

/// State for the Learn screen
#[derive(Debug, Clone, Default)]
pub struct LearnState {
    pub lessons: Vec<LessonSummary>,
    pub selected_index: usize,
    pub viewing_content: bool,
    pub current_content: Option<LessonContent>,
    pub beginner_mode: bool,
    pub loading: bool,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LessonSummary {
    pub id: String,
    pub title: String,
    pub category: String,
    pub duration_minutes: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LessonContent {
    pub id: String,
    pub title: String,
    pub content: String,
    pub key_points: Vec<String>,
}

/// State for the Explorer screen
#[derive(Debug, Clone, Default)]
pub struct ExplorerState {
    pub dataset_type: DatasetType,
    pub signal_data: Option<SignalData>,
    pub viewport_start: usize,
    pub zoom_level: f64,
    pub selected_signal_index: usize,
    pub loading: bool,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum DatasetType {
    #[default]
    Synthetic,
    MitBih,
    PtbXl,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SignalData {
    pub signals: Vec<Vec<f64>>,
    pub labels: Vec<String>,
    pub sample_rate: f64,
    pub total_samples: usize,
}

/// State for the Train screen
#[derive(Debug, Clone, Default)]
pub struct TrainState {
    pub model_type: ModelType,
    pub selected_dataset: DatasetType,
    pub epochs: u32,
    pub learning_rate: f64,
    pub train_split: f64,
    pub training: bool,
    pub current_epoch: u32,
    pub training_progress: f64,
    pub training_metrics: Option<TrainingMetrics>,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ModelType {
    #[default]
    LogisticRegression,
    RandomForest,
    CNN,
}

impl ModelType {
    pub fn as_str(&self) -> &'static str {
        match self {
            ModelType::LogisticRegression => "logistic",
            ModelType::RandomForest => "random_forest",
            ModelType::CNN => "cnn",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrainingMetrics {
    pub accuracy: f64,
    pub precision: f64,
    pub recall: f64,
    pub f1_score: f64,
    pub confusion_matrix: Vec<Vec<u32>>,
    pub class_names: Vec<String>,
    pub explanation: String,
}

/// State for the Predict screen
#[derive(Debug, Clone, Default)]
pub struct PredictState {
    pub available_models: Vec<String>,
    pub selected_model_index: usize,
    pub model_loaded: bool,
    pub signal_loaded: bool,
    pub signal_data: Option<Vec<f64>>,
    pub prediction: Option<PredictionResult>,
    pub explanation: Option<String>,
    pub loading: bool,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PredictionResult {
    pub predicted_class: String,
    pub confidence: f64,
    pub top_predictions: Vec<(String, f64)>,
    pub is_uncertain: bool,
    pub uncertainty_message: Option<String>,
}

/// State for the Quiz screen
#[derive(Debug, Clone, Default)]
pub struct QuizState {
    pub mode: QuizMode,
    pub categories: Vec<String>,
    pub selected_category_index: usize,
    pub current_question: Option<QuizQuestion>,
    pub selected_answer: Option<usize>,
    pub feedback: Option<QuizFeedback>,
    pub score: u32,
    pub total_answered: u32,
    pub streak: u32,
    pub category_stats: HashMap<String, (u32, u32)>, // (correct, total)
    pub loading: bool,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum QuizMode {
    #[default]
    CategorySelect,
    Answering,
    ShowingFeedback,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuizQuestion {
    pub id: String,
    pub question: String,
    pub options: Vec<String>,
    pub category: String,
    pub difficulty: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuizFeedback {
    pub correct: bool,
    pub correct_answer: String,
    pub explanation: String,
}

pub struct App {
    pub current_screen: Screen,
    pub config: Config,
    pub backend: PythonBackend,
    pub backend_status: BackendStatus,
    pub quit_requested: bool,
    
    // Screen-specific state
    pub learn_state: LearnState,
    pub explorer_state: ExplorerState,
    pub train_state: TrainState,
    pub predict_state: PredictState,
    pub quiz_state: QuizState,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackendStatus {
    pub connected: bool,
    pub message: String,
}

impl App {
    pub fn new() -> Result<Self> {
        let config = Config::load_or_default()?;
        let backend = PythonBackend::new()?;

        // Initialize quiz categories
        let mut quiz_state = QuizState::default();
        quiz_state.categories = vec![
            "ECG Basics".to_string(),
            "Wave Identification".to_string(),
            "Intervals".to_string(),
            "Rhythm Recognition".to_string(),
            "ML Metrics".to_string(),
            "Arrhythmias".to_string(),
        ];

        // Initialize train state with defaults
        let mut train_state = TrainState::default();
        train_state.epochs = 10;
        train_state.learning_rate = 0.001;
        train_state.train_split = 0.8;

        // Initialize explorer state
        let mut explorer_state = ExplorerState::default();
        explorer_state.zoom_level = 1.0;

        Ok(Self {
            current_screen: Screen::Home,
            config,
            backend,
            backend_status: BackendStatus {
                connected: false,
                message: "Connecting...".to_string(),
            },
            quit_requested: false,
            learn_state: LearnState {
                beginner_mode: true,
                ..Default::default()
            },
            explorer_state,
            train_state,
            predict_state: PredictState::default(),
            quiz_state,
        })
    }

    pub fn render(&mut self, frame: &mut Frame) {
        match self.current_screen {
            Screen::Home => home::render(frame, self),
            Screen::Learn => learn::render(frame, self),
            Screen::Explorer => explorer::render(frame, self),
            Screen::Train => train::render(frame, self),
            Screen::Predict => predict::render(frame, self),
            Screen::Quiz => quiz::render(frame, self),
            Screen::Help => help::render(frame, self),
        }
    }

    pub fn handle_key(&mut self, key: KeyEvent) -> Result<()> {
        // Global hotkeys
        match key.code {
            KeyCode::Char('h') | KeyCode::Char('H') => {
                self.current_screen = Screen::Home;
                return Ok(());
            }
            KeyCode::Char('l') | KeyCode::Char('L') => {
                self.current_screen = Screen::Learn;
                return Ok(());
            }
            KeyCode::Char('e') | KeyCode::Char('E') => {
                self.current_screen = Screen::Explorer;
                return Ok(());
            }
            KeyCode::Char('t') | KeyCode::Char('T') => {
                self.current_screen = Screen::Train;
                return Ok(());
            }
            KeyCode::Char('p') | KeyCode::Char('P') => {
                self.current_screen = Screen::Predict;
                return Ok(());
            }
            KeyCode::Char('z') | KeyCode::Char('Z') => {
                self.current_screen = Screen::Quiz;
                return Ok(());
            }
            KeyCode::Char('?') => {
                self.current_screen = Screen::Help;
                return Ok(());
            }
            _ => {}
        }

        // Screen-specific handling
        match self.current_screen {
            Screen::Home => home::handle_input(self, key),
            Screen::Learn => learn::handle_input(self, key),
            Screen::Explorer => explorer::handle_input(self, key),
            Screen::Train => train::handle_input(self, key),
            Screen::Predict => predict::handle_input(self, key),
            Screen::Quiz => quiz::handle_input(self, key),
            Screen::Help => help::handle_input(self, key),
        }
    }

    pub fn update(&mut self) -> Result<()> {
        // Check backend status
        if let Ok(status) = self.backend.ping() {
            self.backend_status = BackendStatus {
                connected: true,
                message: format!("Connected - Backend v{}", status.backend_version),
            };
        }

        Ok(())
    }

    pub fn can_quit(&self) -> bool {
        // Can add confirmation logic here
        true
    }
}
