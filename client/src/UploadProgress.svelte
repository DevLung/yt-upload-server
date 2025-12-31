<script>
	const UPLOAD_PROGRESS_ENDPOINT = "/upload-progress";
	const FETCH_ERROR_MSG = "error loading progress";
	const UPDATE_INTERVAL_MS = 5000;
    
	let uploadProgress = $state("loading...");
	let intervalId;

	async function getUploadProgress() {
		try {
			const response = await fetch(UPLOAD_PROGRESS_ENDPOINT);
			if (!response.ok) {
				if (response.status === 304) { // if file hasn't changed
					return;
				}
				uploadProgress = FETCH_ERROR_MSG;
				return;
			}
			uploadProgress = await response.text();
		}
		catch {
			uploadProgress = FETCH_ERROR_MSG;
		}
	}

	// poll getUploadProgress() every UPDATE_INTERVAL_MS starting at mount
	$effect(() => {
		getUploadProgress();
		intervalId = setInterval(getUploadProgress, UPDATE_INTERVAL_MS);
		return () => clearInterval(intervalId);
	});
</script>

<h1>Progress</h1>
<pre>{uploadProgress}</pre>