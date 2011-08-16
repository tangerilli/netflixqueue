$(function() {
    console.debug("Netflix queue plugin init..");
    var queue_html = ("<span class='btnWrap mltBtn mltBtn-s50'>" +
                          "<a class='btn btn-50 watchlk btn-play btn-def' href='#'>" + 
                              "<span class='inr queue_text'>Queue</span></a></span>");
    var queue_button = $(queue_html).click(function() {
        var path_elements = window.location.pathname.split("/");
        var movie_id = path_elements[path_elements.length-1];
        var title = $("h2.title").first().html();
        console.debug("Queuing " + movie_id);
        // TODO: Get user email
        var user_email = "tony@angerilli.ca";
        var current_state = queue_button.find(".queue_text").html();
        console.debug(current_state);
        if (current_state == "Queue")
        {
            $.post("http://localhost:8080/users/" + user_email + "/queue", 
                    {"movie_id":movie_id, "title":title}, 
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
            $.ajax({url:"http://localhost:8080/users/" + user_email + "/queue/" + movie_id, 
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
});