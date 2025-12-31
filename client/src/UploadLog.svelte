<script>
	const UPLOAD_LOG_ENDPOINT = "/upload-log";
	const UPLOAD_LOG_STREAM_ENDPOINT = "/upload-log/stream";
	const FETCH_ERROR_MSG = "error loading log";

	let uploadLog = $state("");
	let eventSource;

	async function getUploadLog() {
		try {
			const response = await fetch(UPLOAD_LOG_ENDPOINT);
			if (!response.ok) {
				uploadLog = FETCH_ERROR_MSG;
				return;
			}
			uploadLog = await response.text();
		}
		catch {
			uploadLog = FETCH_ERROR_MSG;
		}
	}

	$effect(() => {
		getUploadLog();

		eventSource = new EventSource(UPLOAD_LOG_STREAM_ENDPOINT);
		eventSource.onmessage = (event) => {
			uploadLog += event.data + "\n";
		};
		eventSource.onerror = () => {
			eventSource.close();
		};
		return () => eventSource.close();
	});
</script>

<h1>Upload Log</h1>
<pre>{uploadLog}</pre>