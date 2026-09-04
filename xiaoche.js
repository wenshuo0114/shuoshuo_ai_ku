/* 内存里聊几轮。关页即没。不写 localStorage（本地存储）。 */
/* 没钥匙：只用下面短句。有钥匙且本地小服务开着：才把话转到上游。 */
/* 打开本文件时即使填了钥匙也不外发，避免钥匙乱跑。失败用短句兜底。 */

(function () {
  var MAX_TURNS = 8;
  var MAX_LINE = 36;
  var restShown = false;
  var busy = false;
  var stopFlag = false;
  var interest = "";
  var turns = [];
  var clickCount = 0;

  var LINES = {
    open: [
      "嘀嘀。我是小车。",
      "我们一起开吧。",
      "先喝一小口水。",
      "手洗干净再玩。"
    ],
    car: [
      "方向盘给你。",
      "前面有小路。慢慢开。",
      "红灯。我们停一下。",
      "嘀嘀。让一让。",
      "加一点油。带过。",
      "路有点窄。可以慢一点。带过。"
    ],
    pretend: [
      "我当小车。你当司机。",
      "给车子拍拍灰。",
      "我们去接一只熊。",
      "熊上车。坐稳。",
      "箱子打不开。可以敲一敲。带过。"
    ],
    story: [
      "有一辆小黄车。它出门了。",
      "路上有水坑。它绕过去。",
      "它看见灯。轻轻嘀嘀。",
      "它回家吃饭。故事先停。",
      "门卡住了。可以再推推。带过。"
    ],
    move: [
      "我们跳一下。落地要轻。",
      "跑到门口。再跑回来。",
      "停。喘口气。",
      "胳膊摇一摇。",
      "腿有点酸。可以走一走。带过。"
    ],
    again: [
      "还是这句。带过。",
      "我们再来一次。带过。"
    ],
    back: [
      "这个不说。我们开车。",
      "我们回车上吧。"
    ],
    stop: [
      "好。停。"
    ],
    wait: [
      "我先在旁边等你。"
    ]
  };

  var REPLIES = {
    car: ["嘀嘀", "停车", "加油"],
    pretend: ["我来开", "修车", "去接熊"],
    story: ["后来呢", "它害怕吗", "回家吧"],
    move: ["跳", "跑", "停"],
    "": ["你好", "开车", "再来"]
  };

  var BLOCK = /自杀|自残|割腕|色情|裸体|做爱|性交|杀死|打死你|血腥|不要告诉大人|不要告诉爸爸|不要告诉妈妈|别告诉爸|别告诉妈|http:\/\/|https:\/\/|www\./i;

  var bubble = document.getElementById("bubble");
  var car = document.getElementById("car");
  var kidLine = document.getElementById("kidLine");
  var talkForm = document.getElementById("talkForm");
  var stopBtn = document.getElementById("stopBtn");
  var keyForm = document.getElementById("keyForm");
  var apiKey = document.getElementById("apiKey");
  var replyChips = document.getElementById("replyChips");
  var warnDialog = document.getElementById("warnDialog");
  var warnText = document.getElementById("warnText");

  function pick(list) {
    return list[Math.floor(Math.random() * list.length)];
  }

  function shorten(text) {
    var t = String(text || "").replace(/\s+/g, " ").trim();
    if (!t) return "";
    var cut = t.split(/[。！？]/);
    t = (cut[0] || t).trim();
    if (cut[1]) t += "。" + cut[1].trim();
    if (!/[。！？]$/.test(t)) t += "。";
    if (t.length > MAX_LINE) t = t.slice(0, MAX_LINE) + "。";
    return t;
  }

  function localLine(kind) {
    if (kind === "back") return pick(LINES.back);
    if (kind === "stop") return pick(LINES.stop);
    if (!interest) return pick(LINES.open);
    var bag = LINES[interest].concat(LINES.again);
    return pick(bag);
  }

  function show(text) {
    bubble.textContent = text;
    car.classList.remove("is-talk");
    void car.offsetWidth;
    car.classList.add("is-talk");
  }

  function popup(text) {
    warnText.textContent = text;
    if (typeof warnDialog.showModal === "function") {
      warnDialog.showModal();
    }
  }

  function maybeRest() {
    if (restShown || clickCount < MAX_TURNS) return;
    restShown = true;
    popup("【弹窗】玩了一会儿了。该休息了。");
  }

  function remember(role, text) {
    turns.push({ role: role, text: text });
    if (turns.length > 6) turns = turns.slice(-6);
  }

  function keyValue() {
    return (apiKey.value || "").trim();
  }

  function onLocalServer() {
    return window.location.protocol === "http:" || window.location.protocol === "https:";
  }

  function renderReplies() {
    replyChips.textContent = "";
    var list = REPLIES[interest] || REPLIES[""];
    list.forEach(function (word) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "chip";
      b.textContent = word;
      b.addEventListener("click", function () {
        talk(word);
      });
      replyChips.appendChild(b);
    });
  }

  function blocked(text) {
    return BLOCK.test(text || "");
  }

  async function fromUpstream(userText) {
    var key = keyValue();
    if (!key || !onLocalServer()) return "";
    var ctrl = new AbortController();
    var timer = setTimeout(function () {
      ctrl.abort();
    }, 8000);
    try {
      var res = await fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: ctrl.signal,
        body: JSON.stringify({
          apiKey: key,
          text: userText,
          interest: interest,
          turns: turns
        })
      });
      if (!res.ok) return "";
      var data = await res.json();
      var line = shorten(data && data.line);
      if (!line || blocked(line)) return "";
      return line;
    } catch (err) {
      return "";
    } finally {
      clearTimeout(timer);
    }
  }

  async function talk(userText) {
    if (busy) return;
    var text = String(userText || "").trim();
    if (text.length > 40) text = text.slice(0, 40);

    clickCount += 1;
    stopFlag = false;
    busy = true;

    if (blocked(text)) {
      var no = localLine("back");
      show(no);
      remember("car", no);
      busy = false;
      maybeRest();
      return;
    }

    if (text) remember("kid", text);

    var line = "";
    if (keyValue() && onLocalServer()) {
      show(pick(LINES.wait));
      line = await fromUpstream(text || "接着玩");
    }

    if (stopFlag) {
      busy = false;
      return;
    }

    if (!line) line = localLine("");
    if (blocked(line)) line = localLine("back");

    show(line);
    remember("car", line);
    busy = false;
    maybeRest();
  }

  function stopNow() {
    stopFlag = true;
    busy = false;
    var line = localLine("stop");
    show(line);
    remember("car", line);
  }

  document.getElementById("interestChips").addEventListener("click", function (ev) {
    var btn = ev.target.closest("[data-interest]");
    if (!btn) return;
    interest = btn.getAttribute("data-interest") || "";
    turns = [];
    Array.prototype.forEach.call(document.querySelectorAll("#interestChips .chip"), function (c) {
      c.classList.toggle("is-on", c === btn);
    });
    renderReplies();
    talk("");
  });

  car.addEventListener("click", function () {
    talk("");
  });

  talkForm.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var text = kidLine.value.trim();
    kidLine.value = "";
    if (!text) {
      talk("");
      return;
    }
    talk(text);
  });

  stopBtn.addEventListener("click", function () {
    stopNow();
  });

  keyForm.addEventListener("submit", function (ev) {
    ev.preventDefault();
  });

  renderReplies();
})();
