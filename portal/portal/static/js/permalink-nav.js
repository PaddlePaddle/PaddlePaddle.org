
$.fn.immediateText = function() {
    // Returns text of immediate element
    return this.contents().not(this.children()).text();
};

var PermalinkNav = {
    init: function(navContainerSelector) {
        navContainer = $(navContainerSelector);

        if (navContainer.length) {
            permalinks = $("h1:has(a),h2:has(a)");

            if (permalinks.length == 0) {
                navContainer.hide()
            } else {
                $(".doc-content").addClass('with-permalink-nav');

                var containerOl;
                permalinks.each(function(index) {
                    var header = $(this);

                    if (header.is("h1")) {
                        containerOl = $("<ol/>");

                        var link = header.find("a:first").attr("href")
                        var linkElement = $('<a />', { text: header.immediateText(), href: link })
                        containerOl.append(linkElement);
                        navContainer.append(containerOl);

                    } else if (header.is("h2")) {
                        if (containerOl == null) {
                            containerOl = $("<ol/>");
                            navContainer.append(containerOl);
                        }

                        var link = header.find("a:first").attr("href")

                        var linkElement = $('<a />', { text: header.immediateText(), href: link })
                        var containerLi = $("<li/>");
                        containerLi.append(linkElement);
                        containerOl.append(containerLi);
                    }
                });

                var offset = 0;
                var variance = 4;   // Permalinks are slightly below the header content, so we have to adjust for it

                navContainer.find('a[href^="#"]').click(function(event) {
                    // Prevent from default action to intitiate
                    event.preventDefault();

                    //remove active from all anchor and add it to the clicked anchor
                    navContainer.find('a[href^="#"]').removeClass("active")
                    $(this).addClass('active');

                    // The id of the section we want to go to
                    var anchorId = $(this).attr('href');

                    // Our scroll target : the top position of the section that has the id referenced by our href
                    var target = $(anchorId).offset().top - offset;

                    $('html, body').stop().animate({ scrollTop: target }, 500, function () {
                        window.location.hash = anchorId;
                    });

                    return false;
                });

                $(window).scroll(function(){
                    // Get the current vertical position of the scroll bar
                    position = $(this).scrollTop();
                    navContainer.find('a[href^="#"]').each(function(){
                        var anchorId = $(this).attr('href');
                        var target = $(anchorId).offset().top - offset;
                        // check if the document has crossed the page

                        if(position+variance>=target){
                             //remove active from all anchor and add it to the clicked anchor
                            navContainer.find('a[href^="#"]').removeClass("active")
                            $(this).addClass('active');
                        }
                    })
                });

                // Set the first link as active
                navContainer.find('a[href^="#"]').first().addClass('active');
            }
        }
    }
}

$(function(){
    PermalinkNav.init(".permalinks-nav");
})