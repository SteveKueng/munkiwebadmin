function copyTextToClipboard(text) {
    var textArea = document.createElement("textarea");
  
    //
    // *** This styling is an extra step which is likely not required. ***
    //
    // Why is it here? To ensure:
    // 1. the element is able to have focus and selection.
    // 2. if element was to flash render it has minimal visual impact.
    // 3. less flakyness with selection and copying which **might** occur if
    //    the textarea element is not visible.
    //
    // The likelihood is the element won't even render, not even a flash,
    // so some of these are just precautions. However in IE the element
    // is visible whilst the popup box asking the user for permission for
    // the web page to copy to the clipboard.
    //
  
    // Place in top-left corner of screen regardless of scroll position.
    textArea.style.position = 'fixed';
    textArea.style.top = 0;
    textArea.style.left = 0;
  
    // Ensure it has a small width and height. Setting to 1px / 1em
    // doesn't work as this gives a negative w/h on some browsers.
    textArea.style.width = '2em';
    textArea.style.height = '2em';
  
    // We don't need padding, reducing the size if it does flash render.
    textArea.style.padding = 0;
  
    // Clean up any borders.
    textArea.style.border = 'none';
    textArea.style.outline = 'none';
    textArea.style.boxShadow = 'none';
  
    // Avoid flash of white box if rendered for any reason.
    textArea.style.background = 'transparent';
  
    textArea.value = text;
  
    document.body.appendChild(textArea);
  
    textArea.select();
  
    try {
      var successful = document.execCommand('copy');
    } catch (err) {
      console.log('Oops, unable to copy');
    }
  
    document.body.removeChild(textArea);
}

function getRunningMachine() {
    $.ajax({
        method: 'GET',
        url:"/api/report",
        timeout: 10000,
        cache: false,
        success: function(data) {
            // on success
            $(".imagrInprogress").empty()
            var run = 0
            for (var i in data) {
                if(data[i].current_status == "in_progress") {
                    $(".imagrInprogress").prepend('<li><a href="/reports/#'+i+'"><strong>'+data[i].hostname+'</strong><div class="progress"><div class="progress-bar progress-bar-striped progress-bar-animated active" role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%"></div></div></a></li>')
                    run++;
                }
                if(run > 4) {
                    break;
                }
                //console.log(JSON.stringify(data[i]));
            }
            if(run > 0) {
                $(".imagrInprogress").append('<li class="divider"></li><li><a href="/reports/?show=inprogress" class="text-center"><strong>See All </strong><i class="fa fa-angle-right"></i></a></li>')
            } else {
                $(".imagrInprogress").append('<li><a class="text-center">no machine in progress</a></li>');
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
            // on error
        },
    })
}

// Sidebar toggle
const sidebarToggle = document.body.querySelector('#sidebar-toggle');
sidebarToggle.addEventListener('click', function() {
    document.querySelector("#sidebar").classList.toggle('collapsed');
});

$(window).on('resize', function() {
    if($(window).width() < 768) {
        $('#sidebar').addClass('collapsed');
    }
})