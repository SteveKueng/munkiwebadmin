
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (settings.type == 'POST' || settings.type == 'PUT' || settings.type == 'DELETE') {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    }
});

$(document).ready(function() {
	initUpdatesTable();
	fixDropdown();
	
	$('#list_items').on( 'change', 'input.cbox', function () {
		element = $(this).attr('id').split(':')
        id = new Array();
		id[0] = element[0]
		branch = element[1]
        if ($(this).prop("checked")) {
        	addProductToBranch(id, branch);
    	} else {
			removeProductFromBranch(id, branch);
		}
    } );
});

function fixDropdown() {
	// hold onto the drop down menu                                             
  var dropdownMenu;

  // and when you show it, move it to the body                                     
  $('#page-wrapper').on('show.bs.dropdown', function(e) {

    // grab the menu        
    dropdownMenu = $(e.target).find('.dropdown-menu');

    // detach it and append it to the body
    $('body').append(dropdownMenu.detach());   

    // grab the new offset position
    var eOffset = $(e.target).offset();
    if(eOffset.left + dropdownMenu.width() + 5 > $(window).width()) {
        var offsetLeft = $(window).width() - dropdownMenu.width() - 5;
    } else {
        var offsetLeft = eOffset.left
    }
    // make sure to place it where it would normally go (this could be improved)
    dropdownMenu.css({
        'display': 'block',
        'top': eOffset.top + $(e.target).outerHeight(),
        'left': offsetLeft
    });                                             
  });

  // and when you hide it, reattach the drop down, and hide it normally                                                   
  $(window).on('hide.bs.dropdown', function(e) {        
    $(e.target).append(dropdownMenu.detach());        
    dropdownMenu.hide();                              
  });
}

// ---
function initUpdatesTable() {
    // start our monitoring timer loop
    monitor_update_list();
	var columns = dataTableCols('.table-header');
    var table = $('#list_items').DataTable({
        ajax: {
            url: "/updates/",
            cache: false,
            dataSrc: function ( json ) {
                var column_rows = [];
                for ( var i=0 ; i < json.length; i++ ) {
                    column_rows.push(json[i]);
				}
				//console.log(column_rows);
                return column_rows;
            },
            complete: function(jqXHR, textStatus) {
                window.clearInterval(poll_loop);
                $('#process_progress').modal('hide');
            },
            global: false,
        },
		"fnRowCallback": function( nRow, aData, iDisplayIndex, iDisplayIndexFull ) {
			if ( aData['depricated'])
			{
				$('td', nRow).addClass('warning');
			}
		},
		"columns": columns,
		columnDefs: [
			{ targets: [0, 1, 2], "orderable": true },
			{ targets: [0], "className": 'details-control', "width": "auto" },
			{ targets: [1], "width": 50, "className": "left" },
			{ targets: [2], "width": 75 },
			{ "className": "text-center", "width": 20, "targets": "_all", "orderable": false},
			{ targets: [-1], visible: false }
		],
         "sDom": "<t>",
         "bPaginate": false,
         "scrollY": '100%',
         drawCallback: function () { // this gets rid of duplicate headers
            $('.dataTables_scrollBody thead tr').css({ display: 'none' }); 
        },
         //"bScrollCollapse": true,
         "bInfo": false,
         "bFilter": true,
         "bStateSave": false,
         "aaSorting": [[2,'desc']]
     });
     // tie our search field to the table
     var thisTable = $('#list_items').DataTable();
     $('#listSearchField').keyup(function(){
          thisTable.search($(this).val()).draw();
     });

	 // Add event listener for opening and closing details
    $('#list_items tbody').on('click', 'td.details-control', function () {
        var tr = $(this).closest('tr');
        var row = table.row( tr );
 
        if ( row.child.isShown() ) {
            // This row is already open - close it
            row.child.hide();
            tr.removeClass('shown');
        }
        else {
            // Open this row
            row.child( format(row.data()) ).show();
            tr.addClass('shown');
        }
    } );
}

function monitor_update_list() {
    $('#process_progress_title_text').text('Getting updates...')
    $('#process_progress_status_text').text('Processing...')
    poll_loop = setInterval(function() {
            update_status('/updates/__get_update_list_status');
        }, 200);
}

function dataTableCols(id) {
	keylist = ['key', 'title', 'version', 'date', 'depricated']
	columns = $(id).map(function() { 
        item = { "data": $(this).attr('id') };
		return item
  	}).get();;
	return columns
}

/* Formatting function for row details - modify as you need */
function format( d ) {
    // `d` is the original data object for the row
    return '<b>' + d.key + '</b><br><br>' + d.description
}

function filterDatatable(filter) {
    clearFilterDatatable()
    $.fn.dataTableExt.afnFiltering.push(
        function( oSettings, aData, iDataIndex, rowData, counter ) {
            switch(filter) {
                case "depricated":
                    return JSON.parse(aData[aData.length - 1])
                    break;
                case "no-depricated":
                    return !JSON.parse(aData[aData.length - 1])
                    break;
                }
        }
    );
    $('#list_items').dataTable().fnDraw(); // Manually redraw the table after filtering
}

function clearFilterDatatable() {
    $.fn.dataTableExt.afnFiltering.length = 0;
    $('#list_items').dataTable().fnDraw();
}

// add new branch
function newBranch(branch) {
	if(branch != "") {
		$.ajax({
			url: '/updates/new_branch/'+branch,
			type: 'POST',
			contentType: 'application/json; charset=utf-8',
			success: function() {
				location.reload();
			},
            error: function(jqXHR, textStatus, errorThrown) {
            $("#errorModalTitleText").text("create branch error");
             try {
                 var json_data = $.parseJSON(jqXHR.responseText)
                 if (json_data['result'] == 'failed') {
                     $("#errorModalDetailText").text(json_data['detail']);
                     $("#errorModal").modal("show");
                     return;
                 }
             } catch(err) {
                 // do nothing
             }
             $("#errorModalDetailText").text(errorThrown);
             $("#errorModal").modal("show");
          }
		});
	}
} 

function deleteBranch(branch) {
	if(branch != "") {
		$.ajax({
			url: '/updates/delete_branch/'+branch,
			type: 'POST',
			contentType: 'application/json; charset=utf-8',
			success: function() {
				location.reload();
			},
            error: function(jqXHR, textStatus, errorThrown) {
            $("#errorModalTitleText").text("delete branch error");
             try {
                 var json_data = $.parseJSON(jqXHR.responseText)
                 if (json_data['result'] == 'failed') {
                     $("#errorModalDetailText").text(json_data['detail']);
                     $("#errorModal").modal("show");
                     return;
                 }
             } catch(err) {
                 // do nothing
             }
             $("#errorModalDetailText").text(errorThrown);
             $("#errorModal").modal("show");
          }
		});
	}
}

function openDeleteBranchConfirmModal(branch) {
    $('#confirmationModalTitle').text("Delete selected branch?");
	$('#confirmationModalBodyText').html("Really delete <b>"+branch+"</b>?<br>This action cannot be undone.");
	$('#confirmationButton').attr("onclick","deleteBranch('"+branch+"')");
    $('#confirmationButton').text("Delete");
	$('#confirmationModal').modal({
		show: 'true',
	}); 
}

function openAddProductConfirmModal(branch, products) {
    $('#confirmationModalTitle').text("Add products to branch?");
	$('#confirmationModalBodyText').html("Really add <b>"+products+"</b> to <b>"+branch+"</b>?");
	$('#confirmationButton').attr("onclick","addProductToBranch(['"+products+"'], '"+branch+"', true)");
    $('#confirmationButton').text("Add");
	$('#confirmationModal').modal({
		show: 'true',
	}); 
}

function openRemoveProductConfirmModal(branch, products) {
    $('#confirmationModalTitle').text("Remove products from branch?");
	$('#confirmationModalBodyText').html("Really remove <b>"+products+"</b> from <b>"+branch+"</b>?");
	$('#confirmationButton').attr("onclick","removeProductFromBranch(['"+products+"'], '"+branch+"', true)");
    $('#confirmationButton').text("Remove");
	$('#confirmationModal').modal({
		show: 'true',
	}); 
}

function addProductToBranch(products, branch, reload = false) {
	$.ajax({
        url: '/updates/add_product',
        type: 'POST',
        data: {product_id_list: products, branch_name: branch},
        dataType: 'json',
        success: function() {
            if(reload) {
                location.reload();
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $("#errorModalTitleText").text("product add error");
             try {
                 var json_data = $.parseJSON(jqXHR.responseText)
                 if (json_data['result'] == 'failed') {
                     $("#errorModalDetailText").text(json_data['detail']);
                     $("#errorModal").modal("show");
                     return;
                 }
             } catch(err) {
                 // do nothing
             }
             $("#errorModalDetailText").text(errorThrown);
             $("#errorModal").modal("show");
        },
    });
}

function removeProductFromBranch(products, branch, reload = false) {
	$.ajax({
        url: '/updates/remove_product',
        type: 'POST',
        data: {product_id_list: products, branch_name: branch},
        dataType: 'json',
        success: function() {
            if(reload) {
                location.reload();
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $("#errorModalTitleText").text("product remove error");
             try {
                 var json_data = $.parseJSON(jqXHR.responseText)
                 if (json_data['result'] == 'failed') {
                     $("#errorModalDetailText").text(json_data['detail']);
                     $("#errorModal").modal("show");
                     return;
                 }
             } catch(err) {
                 // do nothing
             }
             $("#errorModalDetailText").text(errorThrown);
             $("#errorModal").modal("show");
        }
    });
}