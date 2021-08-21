let startPos;
let currFocusedCanvas;
var baseObjects = [];
var objects = {};
// expanded form
// objects = {
//    'filename': file the pages come from
//    '<canvasID>':{
//        'annotations': [<rect1>, <rect2>]
//        'baseImage': the actual image of a page, use this to draw on canvas
//        'baseImageName': link to image, will be used on python's side
//    },...
//}
var drawing = false;
var editMode = 1; // 0 - delete, 1 - insert
var imagesLoaded = 0;

function drawRect(id, x1, y1, x2, y2){
    var c = document.getElementById(id);
    var ctx = c.getContext("2d");

    var width = Math.abs(x1 - x2);
    var height = Math.abs(y1 - y2);
    var topl = {}, botr = {};
    topl['x'] = Math.min(x1, x2);
    topl['y'] = Math.min(y1, y2);
    botr['x'] = Math.max(x1, x2);
    botr['y'] = Math.max(y1, y2)

    ctx.beginPath();
    ctx.lineWidth = "1";
    ctx.strokeStyle = "black";

    ctx.rect(topl.x, topl.y, width, height);
    ctx.fillStyle = "#33CCCC";
    ctx.globalAlpha = 0.2;
    ctx.fillRect(topl.x, topl.y, width, height);
    ctx.globalAlpha = 1;
    ctx.stroke();
}

function getMousePos(evt, canvas) {
    var rect = canvas.getBoundingClientRect();
    var x, y;
    if (evt.touches){
        x = evt.touches[0].clientX;
        y = evt.touches[0].clientY;
    } else if (evt.changedTouches){
        x = evt.changedTouches[0].clientX;
        y = evt.changedTouches[0].clientY;
    } else {
        x = evt.clientX;
        y = evt.clientY;
    }
    return {
      'x': x - rect.left,
      'y': y - rect.top
    };
}

function update(canvas){
    var ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(objects[canvas.id]['baseImage'], 0, 0);
    for (var prevRects of objects[canvas.id]['annotations']){
        drawRect(canvas.id, prevRects.startX, prevRects.startY, prevRects.endX, prevRects.endY);
    }
}

function handle_click(evt, canvas) {
    currFocusedCanvas = canvas;
    if (editMode == 1) {
        startPos = getMousePos(evt, canvas);
        drawing = true;
    } else {
        targetPos = getMousePos(evt, canvas);
        let counter = 0;

        for (var rect of objects[currFocusedCanvas.id]['annotations']) {
            if (targetPos.x >= rect.startX && targetPos.x <= rect.endX) {
                if (targetPos.y >= rect.startY && targetPos.y <= rect.endY) {
                    objects[currFocusedCanvas.id]['annotations'].splice(counter, 1);
                    update(currFocusedCanvas);
                    break;
                }
            }
            ++counter;
        }
    }
}

function handle_move(evt, canvas) {
    if (drawing) {
        var ctx = canvas.getContext("2d");
        update(canvas);
        let currPos = getMousePos(evt, canvas);
        drawRect(canvas.id, startPos.x, startPos.y, Math.min(currPos.x, canvas.width), Math.min(currPos.y, canvas.height));
    }
}

function handle_release(evt, canvas) {
    if (drawing) {
        var endPos = getMousePos(evt, canvas);
        let coordinates = {"startX" : Math.min(startPos.x, endPos.x), 
                           "startY" : Math.min(startPos.y, endPos.y),
                           "endX" : Math.min(Math.max(startPos.x, endPos.x), canvas.width),
                           "endY" : Math.min(Math.max(startPos.y, endPos.y), canvas.height)
                          }
        if (Math.min(Math.abs(coordinates.endX - coordinates.startX), Math.abs(coordinates.endY - coordinates.startY)) > 10) {
            objects[canvas.id]['annotations'].unshift(coordinates); // add new rects to front
        }
        update(canvas);
        drawing = false;
    }
}

function setBaseImage(src, canvas) {
    var img = new Image();
    img.onload = function() {
        objects[canvas.id]['baseImage'] = img;
        objects[canvas.id]['baseImageName'] = src;
        canvas.width = img.width;
        canvas.height = img.height;
        imagesLoaded++;
        var allLoaded = function() {
            if (imagesLoaded == document.getElementsByClassName.length) {
                for (var base of baseObjects) {
                    var ctx = base.canvas.getContext("2d");
                    ctx.drawImage(base.img, 0, 0);
                }
            }
        };
        allLoaded();
    }
    img.src = src; 
    baseObjects.push({"img" : img, "canvas" : canvas});
}

function switch_mode(evt) {
    if (evt.key == 'd') {
        editMode = 0;
    } else if (evt.key == 'i') {
        editMode = 1;
    }
}

function submitAnnotationsData(){
    return fetch("/edit", {
        method: "POST",
        headers: {'Content-Type':'application/x-www-form-urlencoded'},    
        body: JSON.stringify(objects)
    });
}

window.onload = function(){
    objects['filename'] = 'sample.docx';
    for (var canvas of document.getElementsByClassName("drawRectCanvas")){
        objects[canvas.id] = {};
        objects[canvas.id]['annotations'] = [];
        canvas.addEventListener("mousedown", function(e){handle_click(e, canvas)});
        canvas.addEventListener("mousemove", function(e){handle_move(e, canvas)});
        canvas.addEventListener("mouseup", function(e){handle_release(e, canvas)});
        canvas.addEventListener("touchstart", function(e){handle_click(e, canvas)});
        canvas.addEventListener("touchmove", function(e){handle_move(e, canvas);});
        canvas.addEventListener("touchend", function(e){handle_release(e, canvas)});
        setBaseImage("static/sample.png", canvas);
    }

    document.getElementById('submitAnnotations').addEventListener("click", function(e){
        submitAnnotationsData().then(function(response) {
            console.log(response.status);
            return response.text();
        }).then(function(text) {
            console.log(text);
        });
    });
}

document.addEventListener("keydown", function(e){switch_mode(e)});

document.addEventListener('mousemove', function(e){
    if (drawing){
        handle_move(e, currFocusedCanvas);
    }
});

document.addEventListener('mouseup', function(e){
    if (drawing){
        handle_release(e, currFocusedCanvas);
    }
});
document.addEventListener('touchstart', function(e){
});

document.addEventListener('touchend', function(e){
    //e.preventDefault();
    if (drawing){
        handle_move(e, currFocusedCanvas);
    }
});

document.addEventListener('touchend', function(e){
    if (drawing){
        handle_release(e, currFocusedCanvas);
    }
});


// --- fetch template ---
/*
- Can include request headers 
- Callbacks are returned in type "Promise"
- I don't actually know how they work
- Resources:
https://towardsdatascience.com/talking-to-python-from-javascript-flask-and-the-fetch-api-e0ef3573c451
https://developers.google.com/web/updates/2015/03/introduction-to-fetch
*/
