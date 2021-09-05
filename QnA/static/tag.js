const cont = document.querySelector(".infoContainer");

function checkOption(selectObject) {
    var cur = selectObject.value
    
    // var questionHtml = `<label for="imageTopic">Topic:</label><input type="text" name="imageTopic">`;
    // var answerHtml = `<label for="linkedQuestion">Question:</label><input type="text" name=linkedQuestion:">`;
    var questionHTML = `<p>Hello</p>`
    var answerHTML = `<p>World</p>`;
    console.log(cont.innerHTML);
    if (cur == "question") {
        cont.setAttribute('innerHTML', questionHTML);
    } else {    
        cont.setAttribute('innerHTML', answerHTML);
    }  
    console.log(cont.innerHTML);
}
