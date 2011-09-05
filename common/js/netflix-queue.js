function supports_html5_storage() {
  try {
    return 'localStorage' in window && window['localStorage'] !== null;
  } catch (e) {
    return false;
  }
}

function get_user_email() {
    if(supports_html5_storage())
    {
        return localStorage["netflixqueue_userEmail"];
    }
    return undefined;
}

function getQueryParams(qs) {
    qs = qs.split("+").join(" ");
    var params = {},
        tokens,
        re = /[?&]?([^=]+)=([^&]*)/g;

    while (tokens = re.exec(qs)) {
        params[decodeURIComponent(tokens[1])]
            = decodeURIComponent(tokens[2]);
    }

    return params;
}

function delete_movie(queue_url, movie_id)
{
    $.ajax({url:queue_url + "/" + movie_id,
            type: 'DELETE',
            dataType:"json"});
}

function check_watched(queue_url)
{
    var url = window.location.pathname.split("/");
    var $_GET = getQueryParams(document.location.search);
    console.debug(url);
    if(url[url.length-1] == "WiViewingActivity") {
        console.debug("On activity viewing page");
        $("a.mdpLink").each(function(index, link) {
            link_id = $(link).attr("id");
            movie_id = link_id.slice(2, link_id.length-2);
            delete_movie(queue_url, movie_id);
        });
    }
    if(url[url.length-1] == "WiPlayer") {
        delete_movie(queue_url, $_GET.movieid);
    }
}

function prompt_for_user() {
    var login_div = $("<div id='queue_login'><span class='title'>Netflix Queue Plugin Setup</span>" + 
                      "<label>Email address:</label> <input type='text' id='email'/>" +
                      "<label>Password:</label> <input type='password' id='password'/>" +
                      "<button class='button' id='save_button'>Save</button>" +
                      "<button class='button' id='cancel_button'>Cancel</button></div>");
    if(get_user_email())
    {
        login_div.find("#email").val(get_user_email());
    }
    
    login_div.find("#save_button").click(function () {
        user_email = login_div.find("#email").val();
        password = login_div.find("#password").val();
        hashed_password = hex_md5(password);
        localStorage["netflixqueue_userEmail"] = user_email;
        localStorage["netflixqueue_userPassword"] = hashed_password;
        login_div.slideUp("slow");
    });
    login_div.find("#cancel_button").click(function () {
        login_div.slideUp("slow");
    });
    $("body").prepend(login_div);
    login_div.slideDown(2000);
    console.debug("Prompting for email");
}

function get_queue_url() {
    return "http://localhost:8080/users/" + get_user_email() + "/queue";
}

function get_movie_url(movie_id) {
    return get_queue_url() + "/"+ movie_id;
}

$(function() {
    console.debug("Netflix queue plugin init..");
    var path_elements = window.location.pathname.split("/");
    var movie_id = path_elements[path_elements.length-1];
    
    // See if we can figure out if a movie is/has been watched
    check_watched(get_queue_url());
    
    // Setup the queue button
    $.getJSON(get_movie_url(movie_id), function(data) {
        create_button(data.queued);
    })
    .error(function() { 
        console.debug("Initial request error");
        create_button(false);
    });

    var queue_dialog = $("<div class='dropdown-menu dropdown-profiles' id='outer_queue_dialog'><div id='queue_dialog'>" +
                         "<ul id='queue_list'></ul></div><a href='#' id='configure_link'>Configure Queue Plugin</a></div>");
    queue_dialog.css("position", "absolute");
    queue_dialog.find("#configure_link").click(function() {
        prompt_for_user();
        queue_dialog.hide();
    });
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
        if(!get_user_email())
        {
            prompt_for_user();
            return;
        }
        
        pos = $(this).parent().offset();
        top_pos = pos.top + $(this).innerHeight();
        left_pos = pos.left + $(this).innerWidth() - 200 + 10;
        queue_dialog.css("top", top_pos + "px");
        queue_dialog.css("left", left_pos + "px");
        // Fetch the queue data
        $.getJSON(get_queue_url(), function(data) {
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
                $.post(get_movie_url(movie_id), 
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
                $.ajax({url:get_movie_url(movie_id), 
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