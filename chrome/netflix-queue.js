$(function() {
    console.debug("Netflix queue plugin init..");
    var path_elements = window.location.pathname.split("/");
    var movie_id = path_elements[path_elements.length-1];
    // TODO: Get user email
    var user_email = "tony@angerilli.ca";
    var movie_url = "http://localhost:8080/users/" + user_email + "/queue/" + movie_id
    var queue_url = "http://localhost:8080/users/" + user_email + "/queue";
    
    // Setup the queue button
    $.getJSON(movie_url, function(data) {
        create_button(data.queued);
    })
    .error(function() { 
        console.debug("Initial request error");
        create_button(false);
    });

    var queue_dialog = $("<div class='dropdown-menu dropdown-profiles' id='queue_dialog'><ul id='queue_list'></ul></div>");
    queue_dialog.css("position", "absolute");
    $("body").append(queue_dialog);
    queue_dialog.hover(function() {
        // Need to show the queue as we leave the link and enter the dialog
        queue_dialog.show();
    }, function() {
        queue_dialog.hide();
    });

    var queue_list_item = $("<li class='last-of-type'></li>");

    // Setup the queue list link
    queue_link = $("<a href='#'>View Queue</a>").click(function() {
        pos = $(this).parent().offset();
        top_pos = pos.top + $(this).innerHeight();
        left_pos = pos.left + $(this).innerWidth() - 200 + 10;
        queue_dialog.css("top", top_pos + "px");
        queue_dialog.css("left", left_pos + "px");
        // Fetch the queue data
        $.getJSON(queue_url, function(data) {
            var list_el = queue_dialog.find("#queue_list");
            list_el.empty();
            $.each(data, function(index, queued_item) {
                li = $("<li><a href='" + queued_item.netflix_url + "'>" + queued_item.movie_title + "</a></li>");
                list_el.append(li);
            });
            queue_dialog.show();
        });
    })
    .hover(function() {}, function() {
        queue_dialog.hide();
    });

    queue_list_item.append(queue_link);
    $("#global-tools ul li:last-child").removeClass('last-of-type');
    $("#global-tools ul").append(queue_list_item);

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