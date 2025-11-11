// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use std::process::Command;
use tauri::Manager;

#[derive(Debug, Serialize, Deserialize)]
struct AuditResult {
    url: String,
    status: String,
    output: String,
    error: Option<String>,
}

#[tauri::command]
async fn run_audit(url: String, mode: String) -> Result<AuditResult, String> {
    // Validate URL
    if url.is_empty() {
        return Err("URL cannot be empty".to_string());
    }

    // Determine command based on mode
    let cmd_arg = match mode.as_str() {
        "basic" => "audit",
        "full" => "audit-full",
        "ai" => "audit-ai",
        _ => "audit",
    };

    // Run tinyseoai CLI
    let output = Command::new("tinyseoai")
        .arg(cmd_arg)
        .arg(&url)
        .output();

    match output {
        Ok(result) => {
            let stdout = String::from_utf8_lossy(&result.stdout).to_string();
            let stderr = String::from_utf8_lossy(&result.stderr).to_string();

            if result.status.success() {
                Ok(AuditResult {
                    url: url.clone(),
                    status: "success".to_string(),
                    output: stdout,
                    error: None,
                })
            } else {
                Ok(AuditResult {
                    url: url.clone(),
                    status: "failed".to_string(),
                    output: stdout,
                    error: Some(stderr),
                })
            }
        }
        Err(e) => Err(format!("Failed to execute audit: {}", e)),
    }
}

#[tauri::command]
async fn get_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

#[tauri::command]
async fn check_cli_installed() -> bool {
    Command::new("tinyseoai")
        .arg("--version")
        .output()
        .is_ok()
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            #[cfg(debug_assertions)]
            {
                let window = app.get_webview_window("main").unwrap();
                window.open_devtools();
            }
            Ok(())
        })
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            run_audit,
            get_version,
            check_cli_installed
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
