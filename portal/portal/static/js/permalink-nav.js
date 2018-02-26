/*!
 *   Copyright (c) 2018 PaddlePaddle Authors. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

$.fn.immediateText = function() {
    // Returns text of immediate element
    return this.contents().not(this.children()).text();
};

var PermalinkNav = {
    init: function(navContainerSelector) {
        navContainer = $(navContainerSelector);

        if (navContainer.length) {
            $(navContainer).empty();
            permalinks = $(".doc-content").find("h1,h2,h3");

            if (permalinks.length <= 1) {
                navContainer.hide();
                $(".doc-content").removeClass('with-permalink-nav');
            } else {
                navContainer.show();
                $(".doc-content").addClass('with-permalink-nav');

                var maxIdLength = 30;
                var index = 0;

                var containerRoot = $("<ol/>");
                navContainer.append(containerRoot);

                var containerH1;
                var containerH2;

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

                    if (headerText == '¶') {
                        headerText = '';
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
                        containerH1 = $("<ol/>");
                        containerH2 = null;

                        var link = "#" + headerId;
                        var linkElement = $('<a />', { text: headerText, href: link, title: headerText })
                        var containerLi = $("<li/>");
                        containerLi.append(linkElement);

                        containerRoot.append(containerLi);
                        containerLi.append(containerH1);
                    } else if (header.is("h2")) {
                        var containerId = 'permalink-container-' + index;
                        containerH2 = $("<ol/>", { id: containerId, class: 'collapse' });

                        var link = "#" + headerId;
                        var linkElement = $('<a />', { text: headerText, href: link, title: headerText });
                        var containerLi = $("<li/>");

                        var toggle = $('<i />', { class: 'toggle hidden collapsed far fa-plus-square'});
                        toggle.attr('data-toggle', 'collapse');
                        toggle.attr('data-target', '#' + containerId);

                        containerLi.append(toggle);
                        containerLi.append(linkElement);

                        var container = containerRoot;
                        if (containerH1 != null) {
                            container = containerH1;
                        }

                        container.append(containerLi);
                        containerLi.append(containerH2);
                    } else if (header.is("h3")) {
                        var link = "#" + headerId;
                        var linkElement = $('<a />', { text: headerText, href: link, title: headerText })
                        var containerLi = $("<li/>");
                        containerLi.append(linkElement);

                        var container = containerRoot;
                        if (containerH2 != null) {
                            container = containerH2;
                            $(containerH2).parent().find('.toggle').removeClass('hidden');
                        } else if (containerH1 != null) {
                            container = containerH1;
                        }
                        container.append(containerLi);
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

    $( document ).on( "content-updated", function( event, arg1, arg2 ) {
        PermalinkNav.init(".permalinks-nav");
    });
})