import { mount } from "svelte";
import UploadLog from "./UploadLog.svelte";
import UploadProgress from "./UploadProgress.svelte"

mount(UploadLog, {
    target: document.getElementById("log")
});

mount(UploadProgress, {
    target: document.getElementById("progress")
})