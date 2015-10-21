// Search fields
// Main Search
$(document).ready(function() {
	$('#SearchField').keyup(function(){
		var filter = $(this).val();
		var regExPattern = "gi";
		var regEx = new RegExp(filter, regExPattern);
		$('#listbig a').each(function(){
			if (
				$(this).text().search(new RegExp(filter, "i")) < 0 &&
				$(this).data('state').search(regEx) < 0
				){
					$(this).hide();
				} else {
					$(this).show();
				}
		});
	});
	$('#SearchFieldMobile').keyup(function(){
		var filter = $(this).val();
		var regExPattern = "gi";
		var regEx = new RegExp(filter, regExPattern);
		$('#listbig a').each(function(){
			if (
				$(this).text().search(new RegExp(filter, "i")) < 0 &&
				$(this).data('state').search(regEx) < 0
				){
					$(this).hide();
				} else {
					$(this).show();
				}
		});
	});

	$('#list').click(function(event){
		event.preventDefault();
		setview("list");
		setCookie("view", "list", 7);
	});
	$('#grid').click(function(event){
		event.preventDefault();
		setview("grid");
		setCookie("view", "grid", 7);
	});

	$('#SearchField').change(function(){
		$('#SearchField').keyup();
	});

	$('#SearchFieldMobile').change(function(){
		$('#SearchFieldMobile').keyup();
	});
});

function sideSecific() {
}

function setview(view) {
	if(view == "grid"){
		var view1 = "grid";
		var view2 = "list";
	} else if(view == "list"){
		var view1 = "list";
		var view2 = "grid";
	}
	$("#imgProgress").hide();
	$('#' + view1 + 'view').removeClass('hidden');
	$('#' + view2 + 'view').addClass('hidden');
	$('#' + view1).addClass('open');
	$('#' + view2).removeClass('open');
}
