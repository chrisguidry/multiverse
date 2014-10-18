(function(){
    "use strict";

    var html = document.querySelector('html'),
        header = document.querySelector('header');

    function common() {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 200) {
                if (!header.classList.contains('dismissed')) {
                    header.classList.add('dismissed');
                }
            } else {
                if (header.classList.contains('dismissed')) {
                    header.classList.remove('dismissed');
                }
            }

            if (header.classList.contains('recalled')) {
                header.classList.remove('recalled');
            }
        });

        document.addEventListener('click', function() {
            header.classList.toggle('recalled');
        });
        header.addEventListener('click', function(event) {
            event.stopPropagation();
        });
    }

    function library() {
    }

    function reader() {
        var pageList = document.getElementById('pages'),
            displayTools = document.getElementById('displayTools'),
            displayClasses = [].map.call(displayTools.querySelectorAll('a'), function(el) { return el.id; });

        function selectDisplay(tool) {
            [].forEach.call(document.querySelectorAll('#displayTools>a'), function(otherTool) {
                otherTool.classList.remove('active');
            });
            displayClasses.forEach(function(displayClass) {
                pageList.classList.remove(displayClass);
                html.classList.remove(tool.id);
            });

            tool.classList.add('active');
            html.classList.add(tool.id);
            pageList.classList.add(tool.id);
            [].forEach.call(pageList.querySelectorAll('li'), function(page) {
                page.classList.remove('pure-u-1-1');
                page.classList.remove('pure-u-1-2');
                if (tool.id === 'twoPages') {
                    page.classList.add('pure-u-1-2');
                } else if (tool.id === 'fitWidth' || tool.id === 'fitHeight') {
                    page.classList.add('pure-u-1-1');
                }
            });

            localStorage.setItem('display', tool.id);
        }

        displayTools.addEventListener('click', function(event) {
            event.stopPropagation();
            var tool = event.target;
            if (tool.tagName !== 'A') {
                return;
            }
            selectDisplay(tool);
        });

        document.addEventListener('keyup', function(event) {
            switch (event.keyCode) {
                case 49: // 1
                    selectDisplay(document.getElementById('fitWidth'));
                    break;
                case 50: // 2
                    selectDisplay(document.getElementById('twoPages'));
                    break;
                case 51: // 3
                    selectDisplay(document.getElementById('fitHeight'));
                    break;
                case 52: // 4
                    selectDisplay(document.getElementById('leftToRight'));
                    break;
            }
        });

        if (localStorage.getItem('display')) {
            var initialTool = document.getElementById(localStorage.getItem('display')) ||
                              document.getElementById('fitWidth');
            selectDisplay(initialTool);
        }
    }

    common();
    if (html.classList.contains('library')) {
        library();
    }
    if (html.classList.contains('reader')) {
        reader();
    }
}());
