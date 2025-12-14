use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

pub struct ProgressTracker {
    total_bytes: u64,
    downloaded_bytes: Arc<Mutex<u64>>,
    start_time: Instant,
}

impl ProgressTracker {
    pub fn new(total_bytes: u64) -> Self {
        Self {
            total_bytes,
            downloaded_bytes: Arc::new(Mutex::new(0)),
            start_time: Instant::now(),
        }
    }

    pub fn add_progress(&self, bytes: u64) {
        let mut downloaded = self.downloaded_bytes.lock().unwrap();
        *downloaded += bytes;
    }

    pub fn get_progress(&self) -> f64 {
        let downloaded = *self.downloaded_bytes.lock().unwrap();
        if self.total_bytes > 0 {
            (downloaded as f64 / self.total_bytes as f64) * 100.0
        } else {
            0.0
        }
    }

    pub fn get_speed_kbps(&self) -> f64 {
        let downloaded = *self.downloaded_bytes.lock().unwrap();
        let elapsed = self.start_time.elapsed().as_secs_f64();
        
        if elapsed > 0.0 {
            (downloaded as f64 / 1024.0) / elapsed
        } else {
            0.0
        }
    }

    pub fn get_eta(&self) -> Option<Duration> {
        let downloaded = *self.downloaded_bytes.lock().unwrap();
        let remaining = self.total_bytes.saturating_sub(downloaded);
        
        if remaining == 0 || downloaded == 0 {
            return None;
        }

        let elapsed = self.start_time.elapsed().as_secs_f64();
        let speed = downloaded as f64 / elapsed;
        
        if speed > 0.0 {
            Some(Duration::from_secs_f64(remaining as f64 / speed))
        } else {
            None
        }
    }
}

pub trait ProgressCallback: Send + Sync {
    fn on_progress(&self, downloaded: u64, total: u64, speed_kbps: f64);
}
