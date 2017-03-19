
var HttpClient = function() {
    this.get = function(aUrl, aCallback) {
        var anHttpRequest = new XMLHttpRequest();
        anHttpRequest.onreadystatechange = function() {
            if (anHttpRequest.readyState == 4 && anHttpRequest.status == 200)
                aCallback(anHttpRequest.responseText);
        }

        anHttpRequest.open( "GET", aUrl, true );
        anHttpRequest.send( null );
    }
}

function render_popup(popup_id, endpoint) {
    // Get the modal
    var popUpDiv = document.createElement('div');
    popUpDiv.setAttribute("id", popup_id);
    popUpDiv.setAttribute("class", "popup");
    popUpDiv.setAttribute("style", "display: block");

    var client = new HttpClient;
    client.get(endpoint, function(response) {
        var content = document.createElement('div');
        content.innerHTML = response;

        var popUpContentDiv = document.createElement('div');
        popUpContentDiv.setAttribute("class", "popup-content");

        var content_html = content.getElementsByClassName("page")[0];
        popUpContentDiv.appendChild(content_html);
        popUpDiv.appendChild(popUpContentDiv);
        document.body.appendChild(popUpDiv);
    });

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function(event) {
        if (event.target.id == popup_id) {
            event.target.outerHTML = "";
            delete event.target;
        }
    }

}

function render_popup_content(popup_id, content_text) {
    // Get the modal
    var popUpDiv = document.createElement('div');
    popUpDiv.setAttribute("id", popup_id);
    popUpDiv.setAttribute("class", "popup");
    popUpDiv.setAttribute("style", "display: block");

    var content = document.createElement('div');
    content.innerHTML = content_text;

    var popUpContentDiv = document.createElement('div');
    popUpContentDiv.setAttribute("class", "popup-content");

    var content_html = content.getElementsByClassName("page")[0];
    popUpContentDiv.appendChild(content);
    popUpDiv.appendChild(popUpContentDiv);
    document.body.appendChild(popUpDiv);

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function(event) {
        if (event.target.id == popup_id) {
            event.target.outerHTML = "";
            delete event.target;
        }
    }

}