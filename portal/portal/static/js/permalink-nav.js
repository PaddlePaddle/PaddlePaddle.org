
$.fn.immediateText = function() {
    // Returns text of immediate element
    return this.contents().not(this.children()).text();
};

var PermalinkNav = {
    init: function(navContainerSelector) {
        navContainer = $(navContainerSelector);

        if (navContainer.length) {
            permalinks = $(".doc-content").find("h1,h2");

            if (permalinks.length <= 1) {
                navContainer.hide()
            } else {
                var maxIdLength = 30;

                $(".doc-content").addClass('with-permalink-nav');

                var index = 0;
                var containerOl;
                permalinks.each(function(index) {
                    var header = $(this);

                    var headerId = header.attr('id');
                    var headerText = header.immediateText();

                    if (!headerText && header.has("span")) {
                        firstSpan = header.find("span").first();
                        headerText = firstSpan.text();
                    }

                    if (!headerText && header.has("a")) {
                        firstAnchor = header.find("a").first();
                        headerText = firstAnchor.text();
                    }

                    if (!headerId) {
                        // Create a permalink id on header (if header does not have an id already)
                        headerId = ("permalink-" + index + "-" + headerText.replace(/\W+/g, "-")).toLowerCase();
                        if (headerId > maxIdLength) {
                            headerId = headerId.substring(0, maxIdLength);
                        }
                        header.attr("id", headerId);
                        index++;
                    }

                    if (header.is("h1")) {
                        containerOl = $("<ol/>");
                        var link = "#" + headerId;
                        var linkElement = $('<a />', { text: headerText, href: link, title: headerText })
                        containerOl.append(linkElement);
                        navContainer.append(containerOl);
                    } else if (header.is("h2")) {
                        if (containerOl == null) {
                            containerOl = $("<ol/>");
                            navContainer.append(containerOl);
                        }

                        var link = "#" + headerId;
                        var linkElement = $('<a />', { text: headerText, href: link, title: headerText })
                        var containerLi = $("<li/>");
                        containerLi.append(linkElement);
                        containerOl.append(containerLi);
                    }
                });

                var offset = 0;
                var variance = 4;   // Introduce some variance in px when scrolling to combat any rounding errors
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