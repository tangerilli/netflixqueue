$(function() {
    console.debug("Netflix queue plugin init..");
    var path_elements = window.location.pathname.split("/");
    var movie_id = path_elements[path_elements.length-1];
    // TODO: Get user email
    var user_email = "tony@angerilli.ca";
    var movie_url = "http://localhost:8080/users/" + user_email + "/queue/" + movie_id
    $.getJSON(movie_url, function(data) {
        create_button(data.queued);
    });
    
    function create_button(is_queued) {
        if(is_queued)
        {
            var initial_state = "Unqueue";
        } else {
            var initial_state = "Queue";
        }
        console.debug("Creating button with state " + is_queued + " and text " + initial_state);
        
        var queue_html = ("<span class='btnWrap mltBtn mltBtn-s50'>" +
                          "<a class='btn btn-50 watchlk btn-play btn-def' href='#'>" + 
                          "<span class='inr queue_text'>" + initial_state + "</span></a></span>");
                                  
        var queue_button = $(queue_html).click(function() {        
            var title = $("h2.title").first().html();
            var current_state = queue_button.find(".queue_text").html();
            if (current_state == "Queue")
            {
                $.post(movie_url, 
                        {"title":title}, 
                        function(data, textStatus, jxXHR) {
                            console.debug(data);
                            if (data.result == "ok")
                            {
                                queue_button.find(".queue_text").html("Unqueue");
                            }
                        }, 
                        "json");
            }
            else if (current_state == "Unqueue")
            {
                $.ajax({url:movie_url, 
                        success:function(data, textStatus, jxXHR) {
                            console.debug(data);
                            if (data.result == "ok")
                            {
                                queue_button.find(".queue_text").html("Queue");
                            }
                        },
                        type: 'DELETE',
                        dataType:"json"});
            }
        });
        $("#mdp-actions").append(queue_button);
    }
    
});