$(document).ready(function() {
$('button').on('click',function(e) {
				alert("test");
    if($(this).hasClass('list')) {
			alert("test");
        $('#deviceList').removeClass('grid').addClass('list');
    }
    else if ($(this).hasClass('grid')) {
        $('#deviceList').removeClass('list').addClass('grid');
    }
});
}
