$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (settings.type == 'POST' || settings.type == 'PUT' || settings.type == 'DELETE') {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    }
});

function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    var expires = "expires="+d.toUTCString();
    document.cookie = cname + "=" + cvalue + "; " + expires;
}

function getCookie(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for(var i=0; i<ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1);
        if (c.indexOf(name) != -1) return c.substring(name.length,c.length);
    }
    return "";
}

function windowload() {
	// load stuff form secific side
  sideSecific();

  //cookie for searchfield
	var searchcontent = getCookie("searchcontent");
	document.getElementById("SearchField").value = searchcontent;
  document.getElementById("SearchField").select();

	//press Enter to apply search
	applySearch();

 	//load cookie for grid/list view
  	var view = getCookie("view");
 	  if(! view) {
	 	 view = "grid"
  	}
  	setview(view);
}

$(document).ready(function() {
	$('#SearchField').keyup(function(){
		setCookie("searchcontent", $(this).val(), 0.5 );
	})
});

function applySearch() {
  $('#SearchField').keyup();
}

function addWrapperMargin(height) {
    height = height + 80;
    $('#page-wrapper').animate({ marginTop: height + 'px' , opacity: 1 }, 300);
}

function removeWrapperMargin() {
    $('#page-wrapper').animate({ marginTop: '0px' , opacity: 1 }, 500);
}

function diableSearch() {
    $('#SearchFieldMobile').prop('disabled', true);
    $('#SearchField').prop('disabled', true);
}

function enableSearch() {
    $('#SearchFieldMobile').prop('disabled', false);
    $('#SearchField').prop('disabled', false);
    document.getElementById("SearchField").select();
}
