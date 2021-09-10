function showForm(selectedType) {
    for (let elem of document.getElementsByClassName('question')){
        let visibility = ((selectedType === 'question') ? "block" : "none");
        elem.style.display = visibility;
        elem.labels[0].style.display = visibility;
    }
    for (let elem of document.getElementsByClassName('answer')){
        let visibility = ((selectedType === 'answer') ? "block" : "none");
        elem.style.display = visibility;
        elem.labels[0].style.display = visibility;
    }
}

function setUpImageTypeSelect(){
    let selectQnType = document.getElementById('tag-imageType');
    showForm(selectQnType.value);
    selectQnType.addEventListener("change", function(e){
        let selectQnType = document.getElementById('tag-imageType');
        showForm(selectQnType.value);
    });
}

function setUpPaperSelect(allTitles){
    let paperSelect = document.getElementById('tag-paperSelect');
    let originalValue = paperSelect.value;
    let newChildren = [];
    let nullOption = document.createElement('option');
    nullOption.value = "none";
    nullOption.innerHTML = "Select a paper...";
    newChildren.push(nullOption);
    for (let title of allTitles){
        let selectValue = "";
        let label = title[1];
        if (title[0] === null){
            // use of ^%$ to separate year and title name when passing to server.
            // assumes that no one uses ^%$ as part of their string
            selectValue = "noyear^%$" + label;
            label += " (year: not specified)";
        } else {
            selectValue = title[0].toString() + "^%$" + label;
            label += " (year: " + title[0].toString() + ')';
        }
        let titleOption = document.createElement('option');
        titleOption.value = selectValue;
        if (selectValue === originalValue){
            titleOption.defaultSelected = true;
        }
        titleOption.innerHTML = label;
        newChildren.push(titleOption);
    }
    paperSelect.replaceChildren(...newChildren);
}