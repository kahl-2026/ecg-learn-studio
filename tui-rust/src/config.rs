use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;
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
        Self::load_from_path(&config_path)
    }

    #[allow(dead_code)]
    pub fn save(&self) -> Result<()> {
        let config_path = Self::config_path();
        self.save_to_path(&config_path)
    }

    pub(crate) fn load_from_path(config_path: &Path) -> Result<Self> {
        if config_path.exists() {
            let content = fs::read_to_string(config_path)?;
            let config: Config = toml::from_str(&content)?;
            Ok(config)
        } else {
            Ok(Self::default())
        }
    }

    pub(crate) fn save_to_path(&self, config_path: &Path) -> Result<()> {
        if let Some(parent) = config_path.parent() {
            fs::create_dir_all(parent)?;
        }

        let content = toml::to_string_pretty(self)?;
        fs::write(config_path, content)?;
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

#[cfg(test)]
mod tests {
    use super::{Config, Theme};
    use std::path::PathBuf;
    use tempfile::tempdir;

    #[test]
    fn default_config_is_stable() {
        let config = Config::default();
        assert!(matches!(config.theme, Theme::Default));
        assert_eq!(config.python_path, "python3");
        assert_eq!(config.dataset_dir, PathBuf::from("../datasets"));
    }

    #[test]
    fn save_and_load_round_trip() {
        let dir = tempdir().expect("tempdir should be created");
        let config_path = dir.path().join("ecg-learn-studio").join("config.toml");

        let config = Config {
            theme: Theme::Monochrome,
            python_path: "python3.11".to_string(),
            dataset_dir: PathBuf::from("/tmp/data"),
        };

        config
            .save_to_path(&config_path)
            .expect("config should save successfully");

        let loaded = Config::load_from_path(&config_path).expect("config should load successfully");
        assert!(matches!(loaded.theme, Theme::Monochrome));
        assert_eq!(loaded.python_path, "python3.11");
        assert_eq!(loaded.dataset_dir, PathBuf::from("/tmp/data"));
    }
}
