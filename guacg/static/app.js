// Get display div from document
var display = document.getElementById("display");
var paste = document.getElementById("paste");
// Instantiate client, using an HTTP tunnel for communications.
var guac = new Guacamole.Client(
    new Guacamole.WebSocketTunnel("/ws/")

);

// Add client to display div
display.appendChild(guac.getDisplay().getElement());

// Connect
guac.connect();

display.style.opacity = 1;
paste.style.opacity = 1;
// Error handler
guac.onerror = function(error) {

    console.log(error)
    alert(error.message);
};



// Disconnect on close
window.onunload = function() {
    guac.disconnect();
}
// Mouse
var mouse = new Guacamole.Mouse(guac.getDisplay().getElement());

mouse.onmousedown =
mouse.onmouseup   =
mouse.onmousemove = function(mouseState) {
    guac.sendMouseState(mouseState);
};
 //监听堡垒机端往剪切板复制事件，然后写入文本框中
guac.onclipboard = function(stream, mimetype){
    console.log("监听粘贴板开始")
    if (/^text\//.exec(mimetype)) {
        var stringReader = new Guacamole.StringReader(stream);
        var json = "";
        stringReader.ontext = function ontext(text) {
            json += text
        }

        stringReader.onend = function() {
            console.log("已监听粘贴板结束")
            var clipboardElement = document.getElementById("clipboard");
            clipboardElement.value = '';
            clipboardElement.value = json;
            clipboardElement.select(); // 选择对象
            document.execCommand("Copy");
            console.log('复制成功');
        }
    }

}

 //将内容传送到往堡垒机，data是获取到的文本框中的内容
function setClipboard(data) {
    var stream = guac.createClipboardStream("text/plain");

    var writer = new Guacamole.StringWriter(stream);
    for (var i=0; i<data.length; i += 4096){
        writer.sendText(data.substring(i, i+4096));
    }

    writer.sendEnd();
}
var output = document.querySelector("#output")
var keyboard = new Guacamole.Keyboard(document);
keyboard = new Guacamole.Keyboard(document);


function execKeyboard() {

      keyboard.onkeydown = function (keysym) {

            var clipboard_value = output.value;
            if (keysym == "118" && clipboard_value != ""){
                setClipboard(clipboard_value);
                output.value = "";
            }
            guac.sendKeyEvent(1, keysym);
        };
};

function cancelKeyboard(){
    keyboard.onkeydown = null;
}
function setClipboardData(){
    setClipboard(output.value);
}
keyboard.onkeyup = function (keysym) {
    guac.sendKeyEvent(0, keysym);
};
