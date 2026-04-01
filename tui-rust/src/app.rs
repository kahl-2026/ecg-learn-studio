use anyhow::Result;
use crossterm::event::{KeyCode, KeyEvent};
use ratatui::Frame;
use serde::{Deserialize, Serialize};

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

pub struct App {
    pub current_screen: Screen,
    #[allow(dead_code)]
    pub config: Config,
    pub backend: PythonBackend,
    #[allow(dead_code)]
    pub backend_status: BackendStatus,
    pub quit_requested: bool,
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

        Ok(Self {
            current_screen: Screen::Home,
            config,
            backend,
            backend_status: BackendStatus {
                connected: false,
                message: "Connecting...".to_string(),
            },
            quit_requested: false,
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
