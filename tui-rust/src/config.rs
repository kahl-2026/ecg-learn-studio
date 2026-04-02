use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub theme: Theme,
    pub python_path: String,
    pub dataset_dir: PathBuf,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Theme {
    Default,
    Colorblind,
    Monochrome,
}

impl Config {
    pub fn load_or_default() -> Result<Self> {
        let config_path = Self::config_path();
        
        if config_path.exists() {
            let content = fs::read_to_string(&config_path)?;
            let config: Config = toml::from_str(&content)?;
            Ok(config)
        } else {
            Ok(Self::default())
        }
    }

    #[allow(dead_code)]
    pub fn save(&self) -> Result<()> {
        let config_path = Self::config_path();
        if let Some(parent) = config_path.parent() {
            fs::create_dir_all(parent)?;
        }
        
        let content = toml::to_string_pretty(self)?;
        fs::write(&config_path, content)?;
        Ok(())
    }

    fn config_path() -> PathBuf {
        dirs::config_dir()
            .unwrap_or_else(|| PathBuf::from("."))
            .join("ecg-learn-studio")
            .join("config.toml")
    }
}

impl Default for Config {
    fn default() -> Self {
        Self {
            theme: Theme::Default,
            python_path: "python3".to_string(),
            dataset_dir: PathBuf::from("../datasets"),
        }
    }
}
