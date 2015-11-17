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

// functions
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

	var pkginfo = JSON.stringify(obj);
	//alert(pkginfo)
	$.ajax({
	    type: 'POST',
	    url: "/catalog/save",
	    data: pkginfo,
	    success: function(data) { alert('data: ' + data); },
	    contentType: "application/json",
	    dataType: 'json'
	});

	$('#lgModal').modal('hide')
}

function check(element) {
	$(element).parent().click(function(e) {
			e.stopPropagation();
   });
	$(element).addClass('hidden');
	$(element).next().removeClass('hidden');
}

function uncheck(element) {
	$(element).parent().click(function(e) {
        e.stopPropagation();
   });
	$(element).addClass('hidden');
	$(element).prev().removeClass('hidden');
}
