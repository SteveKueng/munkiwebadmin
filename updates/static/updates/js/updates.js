
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

    // make sure to place it where it would normally go (this could be improved)
    dropdownMenu.css({
        'display': 'block',
        'top': eOffset.top + $(e.target).outerHeight(),
        'left': eOffset.left - $(e.target).width()
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
         "scrollY": '80vh',
         //"bScrollCollapse": true,
         "bInfo": false,
         "bFilter": true,
         "bStateSave": false,
         "aaSorting": [[2,'desc']]
     });
     // start our monitoring timer loop
     monitor_update_list();
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
    	item = { "data": $.trim(this.innerHTML.toLowerCase()) };
		return item
  	}).get();;
	return columns
}

/* Formatting function for row details - modify as you need */
function format ( d ) {
    // `d` is the original data object for the row
    return '<b>' + d.key + '</b><br><br>' + d.description
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
			}
		});
	}
}

function openDeleteModal(branch) {
	$('#branchName').text(branch)
	$('#deleteButton').attr("onclick","deleteBranch('"+branch+"')");
	$('#deleteConfirmationModal').modal({
		show: 'true',
	}); 
}