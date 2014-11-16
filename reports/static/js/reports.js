$(document).ready(function() {
	oTable = $('#dataTables-clients').dataTable({
		"paging":false,
	} );
	$('#SearchField').keyup(function(){
		oTable.fnFilter( $(this).val() );
		var filter = $(this).val();
		var regExPattern = "gi";
		var regEx = new RegExp(filter, regExPattern);
		$('#products li').each(function(){	 
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
		oTable.fnFilter( $(this).val() );
		var filter = $(this).val();
		var regExPattern = "gi";
		var regEx = new RegExp(filter, regExPattern);
		$('#products li').each(function(){	 
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

	$('#SearchField').change(function(){
		$('#SearchField').keyup();
	});

	$('#SearchFieldMobile').change(function(){
		$('#SearchFieldMobile').keyup();
	});
});

$(document).ready(function() {
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
});

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

function sideSecific() { 
}