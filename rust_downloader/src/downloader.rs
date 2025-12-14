use reqwest::{Client, header};
use tokio::fs::{File, OpenOptions};
use tokio::io::{AsyncWriteExt, AsyncSeekExt};
use std::path::PathBuf;
use std::sync::Arc;
use anyhow::{Result, Context};
use futures::stream::{self, StreamExt};

pub struct MultiPartDownloader {
    url: String,
    output_path: PathBuf,
    connections: usize,
    speed_limit_kbps: Option<u64>,
}

impl MultiPartDownloader {
    pub fn new(
        url: String,
        output_path: PathBuf,
        connections: usize,
        speed_limit_kbps: Option<u64>,
    ) -> Result<Self> {
        Ok(Self {
            url,
            output_path,
            connections,
            speed_limit_kbps,
        })
    }

    pub async fn download(&self) -> Result<()> {
        let client = Client::builder()
            .user_agent("FastTubeDownloader/2.0 (Rust)")
            .timeout(std::time::Duration::from_secs(30))
            .build()?;

        // Get file size and check if server supports range requests
        let head_response = client.head(&self.url).send().await?;
        
        let total_size = head_response
            .headers()
            .get(header::CONTENT_LENGTH)
            .and_then(|v| v.to_str().ok())
            .and_then(|s| s.parse::<u64>().ok())
            .context("Failed to get content length")?;

        let accepts_ranges = head_response
            .headers()
            .get(header::ACCEPT_RANGES)
            .and_then(|v| v.to_str().ok())
            .map(|s| s == "bytes")
            .unwrap_or(false);

        if !accepts_ranges || total_size < 1024 * 1024 {
            // Single-threaded download for small files or servers that don't support ranges
            return self.download_single_thread(&client).await;
        }

        // Multi-threaded download
        self.download_multi_thread(&client, total_size).await
    }

    async fn download_single_thread(&self, client: &Client) -> Result<()> {
        let mut response = client.get(&self.url).send().await?;
        let mut file = File::create(&self.output_path).await?;

        while let Some(chunk) = response.chunk().await? {
            file.write_all(&chunk).await?;
        }

        file.sync_all().await?;
        Ok(())
    }

    async fn download_multi_thread(&self, client: &Client, total_size: u64) -> Result<()> {
        // Create the output file
        let mut file = OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .open(&self.output_path)
            .await?;
        
        // Allocate space
        file.set_len(total_size).await?;
        file.sync_all().await?;
        drop(file);

        // Calculate chunk size
        let chunk_size = (total_size + self.connections as u64 - 1) / self.connections as u64;

        // Download chunks concurrently
        let chunks: Vec<_> = (0..self.connections)
            .map(|i| {
                let start = i as u64 * chunk_size;
                let end = std::cmp::min(start + chunk_size - 1, total_size - 1);
                (start, end)
            })
            .collect();

        let client = Arc::new(client.clone());
        let url = Arc::new(self.url.clone());
        let output_path = Arc::new(self.output_path.clone());

        stream::iter(chunks)
            .map(|(start, end)| {
                let client = Arc::clone(&client);
                let url = Arc::clone(&url);
                let output_path = Arc::clone(&output_path);
                
                async move {
                    self.download_chunk(&client, &url, &output_path, start, end).await
                }
            })
            .buffer_unordered(self.connections)
            .collect::<Vec<_>>()
            .await
            .into_iter()
            .collect::<Result<Vec<_>>>()?;

        println!("[Rust] Download complete: {}", self.output_path.display());
        Ok(())
    }

    async fn download_chunk(
        &self,
        client: &Client,
        url: &str,
        output_path: &PathBuf,
        start: u64,
        end: u64,
    ) -> Result<()> {
        let range = format!("bytes={}-{}", start, end);
        
        let mut response = client
            .get(url)
            .header(header::RANGE, range)
            .send()
            .await?;

        let mut file = OpenOptions::new()
            .write(true)
            .open(output_path)
            .await?;
        
        file.seek(std::io::SeekFrom::Start(start)).await?;

        while let Some(chunk) = response.chunk().await? {
            file.write_all(&chunk).await?;
        }

        file.sync_all().await?;
        Ok(())
    }
}
