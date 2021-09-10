var document_select = document.getElementById('select-document');
var paper_select = document.getElementById('select-paper');
var question_select = document.getElementById('select-question')

function update_paper_select(all_papers) {
    var docID = document_select.options[document_select.selectedIndex].value;
    var papers = all_papers[docID];
    let option_html = ``;
    
    for (var paper of papers) {
        var value = "";
        var label = "";
        paper[1] = paper[1].split(' ').join('_'); // html does not like spaces
        if (paper[0] == null) {
            value += "noyear^%$" + paper[1];
            label = paper[1] + " (year: not specified)";
        } else {
            value += paper[0].toString() + "^%$" + paper[1];
            label = paper[1] + ` (year: ${paper[0]})`;
        }
        option_html += `<option value=${value}>${label}</option>`;
    }
    
    paper_select.innerHTML = option_html;
}


function update_question_select(all_questions) {
    var paper = paper_select.options[paper_select.selectedIndex].value.split('^%$')[1];
    paper = paper.split('_').join(' ');
    var questions = all_questions[paper]
    let option_html = ``;
    for (var question of questions) {
        /* [0] - questionID
           [1] - answerID
           [2] - questionNo
           [3] - questionPart
        */
        var value = question[0].toString();
        if (question[3] == "") {
            option_html += `<option value=${value}>${question[2]}</option>`;
        } else {
            option_html += `<option value=${value}>${question[2]} (${question[3]})</option>`;
        }
    }
    question_select.innerHTML = option_html;
}