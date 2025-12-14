# Firefox Interception Note

We've implemented aggressive download interception in the background script.
However, for this to work reliable in Firefox, the user **MUST** grant `downloads` permission.

Since FastTube is a sideloaded extension (for now), the permission request should work automatically because `manifest.firefox.json` includes `"permissions": ["downloads", ...]`.

## Important
Unlike existing link-click interception (content script), this uses `chrome.downloads.onCreated`.
This ensures that **ANY** download started by the browser (even from address bar or redirects) gets caught.
