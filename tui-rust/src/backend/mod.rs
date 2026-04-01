use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::io::{BufRead, BufReader, Write};
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
}

impl PythonBackend {
    pub fn new() -> Result<Self> {
        let mut process = Command::new("python3")
            .arg("-m")
            .arg("ecg_learn.api.server")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()
            .context("Failed to start Python backend")?;

        let stdin = process.stdin.take();
        let stdout = process.stdout.take().map(BufReader::new);

        Ok(Self {
            process: Some(process),
            stdin,
            stdout_reader: stdout,
            request_counter: 0,
        })
    }

    pub fn send_request(&mut self, method: &str, params: serde_json::Value) -> Result<Response> {
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
            stdout.read_line(&mut line)?;
            let response: Response = serde_json::from_str(&line.trim())?;
            Ok(response)
        } else {
            anyhow::bail!("Backend stdout not available");
        }
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

pub mod protocol {
    use super::*;

    pub fn load_data(backend: &mut PythonBackend, dataset_type: &str, count: usize) -> Result<serde_json::Value> {
        let response = backend.send_request("load_data", json!({
            "dataset_type": dataset_type,
            "count": count
        }))?;
        
        if response.success {
            response.result.context("No result in response")
        } else {
            anyhow::bail!("Load data failed: {:?}", response.error);
        }
    }

    pub fn train_model(
        backend: &mut PythonBackend,
        model_type: &str,
        dataset_id: &str
    ) -> Result<serde_json::Value> {
        let response = backend.send_request("train_model", json!({
            "model_type": model_type,
            "dataset_id": dataset_id
        }))?;
        
        if response.success {
            response.result.context("No result in response")
        } else {
            anyhow::bail!("Train model failed: {:?}", response.error);
        }
    }

    pub fn get_lessons(backend: &mut PythonBackend) -> Result<serde_json::Value> {
        let response = backend.send_request("get_lessons", json!({}))?;
        
        if response.success {
            response.result.context("No result in response")
        } else {
            anyhow::bail!("Get lessons failed: {:?}", response.error);
        }
    }
}
