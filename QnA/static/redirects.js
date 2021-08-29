function loadEdit(documentID){
    var obj = {"documentID": documentID};
    fetch("/redirectEdit", {
        method: "POST",
        headers: {'Content-Type':'application/x-www-form-urlencoded'},    
        body: JSON.stringify(obj),
        redirect: "follow",
    }).then(function(response) {
        if (response.redirected){ // Not very safe
            window.location.href = response.url;
        }
    });
}