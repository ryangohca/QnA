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

 window.onload = function(){
     let selectQnType = document.getElementById('tag-imageType');
     showForm('question');
     selectQnType.addEventListener("change", function(e){
         let selectQnType = document.getElementById('tag-imageType');
         showForm(selectQnType.value);
     });
 };