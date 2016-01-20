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
});

$( drag );
$( drop );

// functions
function sideSecific() {
}

function getCatalogItem(catalog_name, catalog_index, item_name, item_version) {
		$('#item_detail').empty();
		$("#item_detail").append('<div class="loading_modal"><div class="text-center" style="padding-top:10px;"><i id="imgProgress" class="fa fa-spinner fa-pulse fa-4x"></i></div></div>');

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

	obj["saveType"] = "pkginfo";
	var pkginfo = JSON.stringify(obj);

	$.post("/catalog/save",
		pkginfo,
		function(data){
			alert("success meldung");
			makecatalogs();
	});
	$('#lgModal').modal('hide');
}

function drag() {
	$('.draggable').draggable({
	  cursor: "auto",
		revert: "invalid",
	  opacity: 0.4,
	  //snap: ".droppable",
		helper: 'clone',
		stack: '.draggable',
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
	var obj = new Object();

	$(ui.draggable).remove();
	var draggableId = ui.draggable.attr("id");
  var droppableId = $(this).attr("id");
	var nameVersion = draggableId.split(':');
	var name = nameVersion[0];
	var version = nameVersion[1];
	var catalog = droppableId;

	obj["name"] = name;
	obj["version"] = version;
	obj["catalog"] = catalog;
	obj["saveType"] = "movePkg";
	var pkginfo = JSON.stringify(obj);

	$.post("/catalog/save",
		pkginfo,
		function(data){
			//alert("success meldung");
			//location.reload();
			makecatalogs();
	});
}

function makecatalogs() {
	//$('.').removeClass('hidden');
	$.get("/catalog/makecatalogs",
		function(data){
			//alert("success meldung");
			location.reload();
	});
}
