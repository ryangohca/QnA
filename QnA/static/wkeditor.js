var document_select = document.getElementById('select-document');
var paper_select = document.getElementById('select-paper');
var question_select = document.getElementById('select-question');

function update_paper_select(all_papers) {
    var docID = document_select.options[document_select.selectedIndex].value;
    var papers = all_papers[docID];
    let new_children = [];
    
    for (var paper of papers) {
        var value = "";
        var label = "";
        if (paper[0] == null) {
            value += "noyear^%$" + paper[1];
            label = paper[1] + " (year: not specified)";
        } else {
            value += paper[0].toString() + "^%$" + paper[1];
            label = paper[1] + ` (year: ${paper[0]})`;
        }
        var new_option = document.createElement('option');
        new_option.value = value;
        new_option.innerHTML = label;
        new_children.push(new_option);
    }
    
    paper_select.replaceChildren(...new_children);
}


function update_question_select(all_questions) {
    var paper = paper_select.options[paper_select.selectedIndex].value.split('^%$')[1];
    var questions = all_questions[paper];
    let new_children = [];
    for (var question of questions) {
        /* [0] - questionID
           [1] - answerID
           [2] - questionNo
           [3] - questionPart
        */
        var value = question[0].toString();
        var label = question[2];
        if (question[3] !== "") {
            label += ` (${question[3]})`;
        }
        var new_option = document.createElement('option');
        new_option.value = value;
        new_option.innerHTML = label;
        new_children.push(new_option);
    }
    question_select.replaceChildren(...new_children);
}

function addQuestion(){
    var questionID = question_select.value;
    document.getElementById("questions").value += questionID + ',';
    document.getElementById("submitform").submit();
}