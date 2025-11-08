// This is a wrapper for background.js to be used with Manifest V2 (Firefox)
// It simulates a non-persistent background script environment for better compatibility.
try {
  importScripts('background.js');
} catch (e) {
  console.error(e);
}
