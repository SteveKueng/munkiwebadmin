$(document).on('click','.grid_list', function (e) {
	    if($(this).hasClass('list')) {
	        $('#deviceList').removeClass('grid').addClass('list');
	    }
	    else if ($(this).hasClass('grid')) {
	        $('#deviceList').removeClass('list').addClass('grid');
	    }
});

$(document).on('keyup','#listSearchField', function () {
	filter = $(this).val();
	$("#deviceList li").each(function() {
    if ($(this).text().search(new RegExp(filter, "i")) > -1) {
      $(this).show();
    } else {
      $(this).hide();
    }
  });
});
