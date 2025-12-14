use pyo3::prelude::*;
use pyo3::types::PyModule;
use pyo3::Bound;
use pyo3::exceptions::PyRuntimeError;
use reqwest::Client;
use tokio::runtime::Runtime;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use anyhow::Result;

mod downloader;
mod progress;

use downloader::MultiPartDownloader;
use progress::ProgressCallback;

/// Download a file with multiple connections
#[pyfunction]
fn download_file(
    py: Python,
    url: String,
    output_path: String,
    connections: Option<usize>,
    speed_limit_kbps: Option<u64>,
) -> PyResult<()> {
    let rt = Runtime::new().map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

    py.allow_threads(|| {
        rt.block_on(async {
            let downloader = MultiPartDownloader::new(
                url,
                PathBuf::from(output_path),
                connections.unwrap_or(16),
                speed_limit_kbps,
            )?;
            
            downloader.download().await
        })
    }).map_err(|e: anyhow::Error| PyRuntimeError::new_err(e.to_string()))
}

/// Download multiple files concurrently
#[pyfunction]
fn download_batch(
    py: Python,
    urls: Vec<String>,
    output_dir: String,
    connections: Option<usize>,
    max_concurrent: Option<usize>,
) -> PyResult<Vec<String>> {
    let rt = Runtime::new().map_err(|e| PyRuntimeError::new_err(e.to_string()))?;
    
    py.allow_threads(|| {
        rt.block_on(async {
            let results = Arc::new(Mutex::new(Vec::new()));
            let semaphore = Arc::new(tokio::sync::Semaphore::new(max_concurrent.unwrap_or(3)));
            
            let mut handles = vec![];
            
            for url in urls {
                let permit = semaphore.clone().acquire_owned().await.unwrap();
                let output_dir = output_dir.clone();
                let results = Arc::clone(&results);
                let connections = connections.unwrap_or(16);
                
                let handle = tokio::spawn(async move {
                    let filename = url.split('/').last().unwrap_or("download").to_string();
                    let output_path = PathBuf::from(&output_dir).join(&filename);
                    
                    let downloader = MultiPartDownloader::new(
                        url.clone(),
                        output_path.clone(),
                        connections,
                        None,
                    )?;
                    
                    match downloader.download().await {
                        Ok(_) => {
                            results.lock().unwrap().push(output_path.to_string_lossy().to_string());
                            Ok(())
                        }
                        Err(e) => Err(e)
                    }
                });
                
                handles.push(handle);
            }
            
            for handle in handles {
                handle.await.map_err(|e| anyhow::anyhow!(e))??;
            }
            
            Ok(Arc::try_unwrap(results).unwrap().into_inner().unwrap())
        })
    }).map_err(|e: anyhow::Error| PyRuntimeError::new_err(e.to_string()))
}

/// Get file size without downloading
#[pyfunction]
fn get_file_size(py: Python, url: String) -> PyResult<u64> {
    let rt = Runtime::new().map_err(|e| PyRuntimeError::new_err(e.to_string()))?;
    
    py.allow_threads(|| {
        rt.block_on(async {
            let client = Client::builder()
                .user_agent("FastTubeDownloader/2.0")
                .build()?;
            
            let response = client.head(&url).send().await?;
            
            let size = response
                .headers()
                .get(reqwest::header::CONTENT_LENGTH)
                .and_then(|v| v.to_str().ok())
                .and_then(|s| s.parse().ok())
                .unwrap_or(0);
            
            Ok(size)
        })
    }).map_err(|e: anyhow::Error| PyRuntimeError::new_err(e.to_string()))
}

#[pymodule]
fn fasttube_downloader(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(download_file, m)?)?;
    m.add_function(wrap_pyfunction!(download_batch, m)?)?;
    m.add_function(wrap_pyfunction!(get_file_size, m)?)?;
    Ok(())
}
