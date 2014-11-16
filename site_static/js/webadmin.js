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