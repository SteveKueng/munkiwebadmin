$(document).ready(function() {
	oTable = $('#dataTables-clients').dataTable({
		"paging":false,
		"aoColumns": [
      { "bSortable": false },
      null,
      null
    ]});
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

	$('#list').click(function(event){
		event.preventDefault();
		setCookie("view_catalogs", "list", 7);
		window.location.reload();
	});
	$('#grid').click(function(event){
		event.preventDefault();
		setCookie("view_catalogs", "grid", 7);
		window.location.reload();
	});

	$('#SearchField').change(function(){
		$('#SearchField').keyup();
	});

	$('#SearchFieldMobile').change(function(){
		$('#SearchFieldMobile').keyup();
	});

	$('#lgModal').on('hidden.bs.modal', function () {
		$('#item_detail').empty();
    $("#item_detail").append('<i id="imgProgress" class="fa fa-spinner fa-pulse fa-4x"></i>');
})
});

$( drag );
$( drop );

// functions
function sideSecific() {
}

function getCatalogItem(catalog_name, catalog_index, item_name, item_version) {
    var catalogItemURL = '/catalog/' + catalog_name + '/' + catalog_index + '/';
    $.get(catalogItemURL, function(data) {
        $('#item_detail').html(data);
    });

		// add modalhead
		$('#lgModal').children().children().append($('.softwareversion[id="' + item_name + '"]').detach())
		// make modal head visible
		$('.softwareversion[id!="' + item_name + '"]').addClass('hidden');
		$('.softwareversion[id="' + item_name + '"]').removeClass('hidden');
		$('.activetabs[id="' + item_version + '"]').addClass('active');
		$('.activetabs[id!="' + item_version + '"]').removeClass('active');
		$('.nav-tabs').tabdrop('layout');

		$('#lgModal').children().children().append($('.modal-body').detach());
		$('.list-group-item[id="' + item_name + '"]').addClass('active');
    $('.list-group-item[id!="' + item_name + '"]').removeClass('active');

		$('#lgModal').children().children().append($('.modal-footer').detach());
		$('.modal-body').removeClass('hidden');
		$('.modal-footer').removeClass('hidden');

		// launch modal / backdrop dosn't close on klick
		$('#lgModal').modal({ backdrop: "static" });
}

function savePkgInfo() {
	//alert("test");
	var obj = new Object();
	$( ".pkginfo_strings" ).each(function() {
		key = $(this).attr('id');
		value = $(this).val();
		obj[key] = value;
	});

	obj['catalogs'] = []
	$( ".pkginfo_catalogs" ).each(function() {
		if ( $(this).prop('checked') ) {
		 value = $(this).val();
		 obj['catalogs'].push(value)
	 }
 	});

	obj["type"] = "test";
	var pkginfo = JSON.stringify(obj);
	alert(pkginfo)
	$.ajax({
	    type: 'POST',
	    url: "/catalog/save",
	    data: pkginfo,
	    success: function(data) { alert('data: ' + data); },
	    contentType: "application/json",
	    dataType: 'json'
	});
	$('#lgModal').modal('hide');
	$('#item_detail').empty();
	$("#item_detail").append('<i id="imgProgress" class="fa fa-spinner fa-pulse fa-4x"></i>');
}

function drag() {
	$('.draggable').draggable({
	  cursor: "move",
		revert: "invalid",
	  opacity: 0.4,
	  snap: ".droppable",
	});
}

function drop() {
	$('.droppable').droppable({
	  accept: ".draggable",
	  hoverClass: 'hovered',
	  drop: move_pkg
	});
}

function move_pkg(event, ui) {
	$(ui.draggable).remove();
	var draggableId = ui.draggable.attr("id");
  var droppableId = $(this).attr("id");

}
