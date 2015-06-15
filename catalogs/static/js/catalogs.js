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

	$('#SearchField').change(function(){
		$('#SearchField').keyup();
	});

	$('#SearchFieldMobile').change(function(){
		$('#SearchFieldMobile').keyup();
	});
});

function getCatalogItem(catalog_name, catalog_index, item_name, item_version)     {
    var catalogItemURL = '/catalog/' + catalog_name + '/' + catalog_index + '/';
    $.get(catalogItemURL, function(data) {
        $('#item_detail').html(data);
    });
    $('.list-group-item[id="' + item_name + '"]').addClass('active');
    $('.list-group-item[id!="' + item_name + '"]').removeClass('active');
	$('.softwareversion[id!="' + item_name + '"]').addClass('hidden');
	$('.softwareversion[id="' + item_name + '"]').removeClass('hidden');
	$('.activetabs[id="' + item_version + '"]').addClass('active');
	$('.activetabs[id!="' + item_version + '"]').removeClass('active');
	$('.nav-tabs').tabdrop('layout');
}

function sideSecific() {
}

function setviews() {
}