use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};

#[derive(Debug, Serialize, Deserialize)]
pub struct Request {
    pub id: String,
    pub version: String,
    pub method: String,
    pub params: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Response {
    pub id: String,
    pub version: String,
    pub success: bool,
    pub result: Option<serde_json::Value>,
    pub error: Option<ErrorInfo>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ErrorInfo {
    pub code: String,
    pub message: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PingResponse {
    pub status: String,
    pub backend_version: String,
    pub python_version: String,
}

pub struct PythonBackend {
    process: Option<Child>,
    stdin: Option<ChildStdin>,
    stdout_reader: Option<BufReader<ChildStdout>>,
    request_counter: u64,
    startup_error: Option<String>,
}

impl PythonBackend {
    pub fn new(python_path: &str) -> Result<Self> {
        let backend_dir = find_backend_dir();
        let mut startup_error = None;
        let mut process = None;
        let mut stdin = None;
        let mut stdout_reader = None;

        if let Some(dir) = backend_dir {
            match Command::new(python_path)
                .arg("-m")
                .arg("ecg_learn.api.server")
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::inherit())
                .current_dir(&dir)
                .spawn()
            {
                Ok(mut child) => {
                    stdin = child.stdin.take();
                    stdout_reader = child.stdout.take().map(BufReader::new);
                    process = Some(child);
                }
                Err(err) => {
                    startup_error = Some(format!(
                        "Failed to start backend with '{}': {}",
                        python_path, err
                    ));
                }
            }
        } else {
            startup_error = Some(
                "Could not locate ml-python/src; backend unavailable".to_string(),
            );
        }

        Ok(Self {
            process,
            stdin,
            stdout_reader,
            request_counter: 0,
            startup_error,
        })
    }

    pub fn startup_error(&self) -> Option<&str> {
        self.startup_error.as_deref()
    }

    pub fn has_process(&self) -> bool {
        self.process.is_some()
    }

    pub fn send_request(&mut self, method: &str, params: serde_json::Value) -> Result<Response> {
        if self.process.is_none() {
            let reason = self
                .startup_error
                .as_deref()
                .unwrap_or("backend process is not running");
            anyhow::bail!("Python backend unavailable: {}", reason);
        }

        self.request_counter += 1;
        let request = Request {
            id: format!("req_{}", self.request_counter),
            version: "1.0".to_string(),
            method: method.to_string(),
            params,
        };

        // Send request
        if let Some(ref mut stdin) = self.stdin {
            let request_json = serde_json::to_string(&request)?;
            writeln!(stdin, "{}", request_json)?;
            stdin.flush()?;
        } else {
            anyhow::bail!("Backend stdin not available");
        }

        // Read response
        if let Some(ref mut stdout) = self.stdout_reader {
            let mut line = String::new();
            stdout.read_line(&mut line).context("Failed to read backend response")?;
            if line.trim().is_empty() {
                anyhow::bail!("Backend returned an empty response");
            }
            let response: Response = serde_json::from_str(&line.trim())?;
            Ok(response)
        } else {
            anyhow::bail!("Backend stdout not available");
        }
    }

    /// Generic request method that returns raw JSON response
    /// Used by UI screens for flexible backend communication
    pub fn request(&mut self, method: &str, params: serde_json::Value) -> Result<serde_json::Value> {
        let response = self.send_request(method, params)?;
        
        // Convert Response struct to JSON Value for UI consumption
        Ok(json!({
            "id": response.id,
            "success": response.success,
            "result": response.result,
            "error": response.error
        }))
    }

    pub fn ping(&mut self) -> Result<PingResponse> {
        let response = self.send_request("ping", json!({}))?;
        
        if response.success {
            if let Some(result) = response.result {
                let ping_response: PingResponse = serde_json::from_value(result)?;
                Ok(ping_response)
            } else {
                anyhow::bail!("Empty ping response");
            }
        } else {
            anyhow::bail!("Ping failed: {:?}", response.error);
        }
    }
}

impl Drop for PythonBackend {
    fn drop(&mut self) {
        if let Some(ref mut process) = self.process {
            let _ = process.kill();
            let _ = process.wait();
        }
    }
}

fn is_backend_src_dir(path: &Path) -> bool {
    path.join("ecg_learn")
        .join("api")
        .join("server.py")
        .exists()
}

fn find_backend_dir() -> Option<PathBuf> {
    let relative_candidates = [
        PathBuf::from("ml-python/src"),
        PathBuf::from("../ml-python/src"),
        PathBuf::from("../../ml-python/src"),
    ];

    for candidate in relative_candidates {
        if is_backend_src_dir(&candidate) {
            return Some(candidate);
        }
    }

    if let Ok(exe_path) = std::env::current_exe() {
        for ancestor in exe_path.ancestors().take(8) {
            let candidate = ancestor.join("ml-python/src");
            if is_backend_src_dir(&candidate) {
                return Some(candidate);
            }
        }
    }

    None
}
