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

var ContentLinksNav = {
    navContainer: null,

    init: function(navContainerSelector) {
        self = this
        self.navContainer = $(navContainerSelector);

        if (self.navContainer.length) {
            self.navContainer.find("a").click(function(e) {
                jqLink = $(this);
                url = jqLink.attr('href');

                if (!url.startsWith('#')) {
                    if (url != document.location.href) {
                        if (history.pushState) {
                            window.history.pushState(url, document.title, url);
                        } else {
                            document.location.href = url;
                        }
                        self.updatePage(url, function() {});
                    }
                    e.preventDefault();
                    e.stopPropagation();
                }
            });
        }
    },

    updatePage: function(url, callback) {
        self = this;
        staticOnlyUrl = url + "?raw=1";
        $.get(staticOnlyUrl, function(staticData) {
            $('#doc-content').html(staticData);
            $('html').scrollTop(0);

            if (callback) {
                callback();
            }

            self.updateActiveLinks();
            $( document ).trigger( "content-updated" );
        });
    },

    updateActiveLinks: function() {
        if (this.navContainer.length) {
            this.navContainer.find("a").each(function(index, anchor) {
                jqAnchor = $(anchor);
                jqAnchorLink = jqAnchor.attr('href');

                if (jqAnchorLink == document.location.pathname) {
                    jqAnchor.addClass('active');

                    var parent = jqAnchor.closest('.chapter');
                    if (parent) {
                        var parentLink = parent.find('h3>a');
                        if (parentLink) {
                            parentLink.addClass('active');
                        }
                    }
                } else {
                    jqAnchor.removeClass('active');
                }
            });

        }
    }
}

$(function(){
    ContentLinksNav.init(".content-links");

    window.onpopstate = function(e){
        if(e.state){
            ContentLinksNav.updatePage(e.state);
        }
    };

    $( document ).on( "content-updated", function( event ) {
        $('#sidebar-nav').removeClass('show');
    });
})
