
let startPos;
var drawing = false;
let currFocusedCanvas;
var objects = {};
var baseImage = {};

function drawRect(id, topx, topy, botx, boty){
    var c = document.getElementById(id);
    var ctx = c.getContext("2d");
    
    ctx.beginPath();
    ctx.lineWidth = "1";
    ctx.strokeStyle = "black";

    ctx.rect(topx, topy, Math.max(1, botx-topx), Math.max(1, boty-topy));
    ctx.fillStyle = "#33CCCC";
    ctx.globalAlpha = 0.2;
    ctx.fillRect(topx, topy, Math.max(1, botx-topx), Math.max(1, boty-topy));
    ctx.globalAlpha = 1;
    ctx.stroke();

}

function getMousePos(evt, canvas) {
    var rect = canvas.getBoundingClientRect();
    return {
      x: evt.clientX - rect.left,
      y: evt.clientY - rect.top
    };
}

function redraw(canvas){
    var ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(baseImage[canvas.id], 0, 0);
    for (var prevRects of objects[canvas.id]){
        drawRect(canvas.id, prevRects.startX, prevRects.startY, prevRects.endX, prevRects.endY);
    }
}

function handle_click(evt, canvas) {
    startPos = getMousePos(evt, canvas);
    currFocusedCanvas = canvas;
    drawing = true;
}

function handle_move(evt, canvas) {
    if (drawing) {
        var ctx = canvas.getContext("2d");
        redraw(canvas);
        let currPos = getMousePos(evt, canvas);
        drawRect(canvas.id, startPos.x, startPos.y, Math.min(currPos.x, canvas.width), Math.min(currPos.y, canvas.height));
    }
}

function handle_release(evt, canvas) {
    if (drawing) {
        drawing = false;
        var endPos = getMousePos(evt, canvas);
        console.log(endPos);
        let coordinates = {"startX" : startPos.x, 
                           "startY" : startPos.y,
                           "endX" : Math.min(endPos.x, canvas.width),
                           "endY" : Math.min(endPos.y, canvas.height)};
        console.log(coordinates);
        if (Math.min(coordinates.endX - coordinates.startX, coordinates.endY - coordinates.startY) > 10) {   
            objects[canvas.id].push(coordinates);
            console.log(objects);
        }
        redraw(canvas);
    }
}

function switch_mode(evt) {
    console.log(evt.code);
}

function setBaseImage(src, canvas) {
    var img = new Image();
    img.src = src;
    img.onload = function() {
        var ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        baseImage[canvas.id] = img;
        canvas.width = img.width;
        canvas.height = img.height;
    }
    
}

window.onload = function(){
    //drawRect("picture", 0, 0, 100, 100);
    for (var canvas of document.getElementsByClassName("drawRectCanvas")){
        // canvas.addEventListener('mousedown', function(){drawRect(canvas.id, 0,0, 100, 100)});
        objects[canvas.id] = [];
        setBaseImage('static/sample.png', canvas);
        canvas.addEventListener("mousedown", function(e){handle_click(e, canvas)});
        canvas.addEventListener("mousemove", function(e){handle_move(e, canvas)});
        canvas.addEventListener("mouseup", function(e){handle_release(e, canvas)});
    }
    canvas.addEventListener("keydown", switch_mode);
}

window.addEventListener('mousemove', function(e){
    if (drawing){
        handle_move(e, currFocusedCanvas);
        // drawing = false;
    }
});

window.addEventListener('mouseup', function(e){
    if (drawing){
        handle_release(e, currFocusedCanvas);
        // drawing = false;
    }
});