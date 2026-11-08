let isLoading = false;

// 回车发送
document.getElementById("question").addEventListener("keydown", e => {
    if (e.key === "Enter") ask();
});

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

async function ask() {
    // ① 请求进行中，禁止再次发送
    if (isLoading) return;

    const input = document.getElementById("question");
    const btn = document.querySelector(".input-row button");
    const q = input.value.trim();

    // ④ 空文本提示优化：红框抖动 + placeholder 提示，1.5s 后恢复
    if (!q) {
        input.classList.add("input-error");
        input.placeholder = "请输入问题后再发送～";
        setTimeout(() => {
            input.classList.remove("input-error");
            input.placeholder = "输入你的问题...";
        }, 1500);
        input.focus();
        return;
    }

    const box = document.getElementById("chat-box");

    // 显示用户问题（转义防 XSS）
    box.innerHTML += `<p><b>你：</b>${escapeHtml(q)}</p>`;
    input.value = "";

    // ② 准备 AI 回答占位：先显示"思考中..."动画
    const aiP = document.createElement("p");
    aiP.innerHTML = '<b>AI：</b><span class="thinking">思考中<span class="dots"></span></span>';
    box.appendChild(aiP);
    let aiText = aiP.querySelector(".thinking");
    let firstChunk = true;

    // 锁定输入区
    isLoading = true;
    input.disabled = true;
    btn.disabled = true;
    btn.textContent = "思考中...";

    try {
        const resp = await fetch("http://127.0.0.1:8000/ask/stream", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({question: q})
        });

        // ① HTTP 非 2xx 视为异常
        if (!resp.ok) throw new Error("HTTP " + resp.status);

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const {done, value} = await reader.read();
            if (done) break;
            const text = decoder.decode(value);
            for (const line of text.split("\n")) {
                if (line.startsWith("data: ")) {
                    const data = line.slice(6);
                    if (data === "[DONE]") break;
                    try {
                        const obj = JSON.parse(data);
                        // 收到第一段 delta，把"思考中"动画替换为实际内容
                        if (firstChunk) {
                            aiText.classList.remove("thinking");
                            aiText.textContent = "";
                            firstChunk = false;
                        }
                        aiText.textContent += obj.delta;
                    } catch (e) { /* 忽略解析失败的行 */ }
                }
            }
            box.scrollTop = box.scrollHeight;
        }

        // 全程没有收到任何内容 → 服务异常
        if (firstChunk) {
            aiP.innerHTML = "<b>AI：</b>当前服务异常，请稍后重试。";
        }
    } catch (e) {
        // ① 网络错误 / 接口异常 → 统一提示
        aiP.innerHTML = "<b>AI：</b>当前服务异常，请稍后重试。";
    } finally {
        // 解锁，恢复输入
        isLoading = false;
        input.disabled = false;
        btn.disabled = false;
        btn.textContent = "发送";
        input.focus();
        box.scrollTop = box.scrollHeight;
    }
}
