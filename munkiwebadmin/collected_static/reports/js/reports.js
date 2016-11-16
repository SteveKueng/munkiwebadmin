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

	$('#list').click(function(event){
		event.preventDefault();
		setCookie("view", "list", 7);
		window.location.reload();
	});
	$('#grid').click(function(event){
		event.preventDefault();
		setCookie("view", "grid", 7);
		window.location.reload();
	});
});

function sideSecific() {
}
