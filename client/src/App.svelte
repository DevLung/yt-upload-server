<script>
	let log = $state("loading...");
	async function getLog() {
		fetch("/log")
		.then(response => response.text())
		.then(data => {log = data});
	}
	getLog();
</script>

<h1>Upload Log</h1>
<button onclick={getLog}>refresh</button>
<p>{log} hi</p>