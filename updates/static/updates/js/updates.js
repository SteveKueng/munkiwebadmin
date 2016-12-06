
var queue = [];
var queueId = 0;

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
});

function addtoqueue(id, branch, listed) {
	// add product to queue list
	queue.push({"id": queueId, "productId": id, "branch": branch, "listed": listed});
	
	// change button
	$("#"+id+'.'+branch).replaceWith( "<button id=\""+ id +"\" onclick='removequeue(\""+ id +"\", \""+ branch +"\", \""+ listed +"\", \""+queueId+"\")' class=\"btn btn-sm "+branch+" btn-info\"><span class=\"glyphicon glyphicon-plus\" aria-hidden=\"true\"></span> Queued</button>" );


	// increase number on apply button
	var $number = $('#queue');
	$number.html((parseInt($number.html(),10) || 0) + 1);
	// alert(JSON.stringify(queue));
	queueId = queueId + 1;
}

function removequeue(id, branch, listed, index) {
	// remove product from queue list
	findAndRemove(queue, "id", index);

	// change button
	if (listed == "true") {
    	$("#"+id+'.'+branch).replaceWith( "<button id=\""+ id +"\" onclick='addtoqueue(\""+ id +"\", \""+ branch +"\", \""+ listed +"\")' class=\"btn btn-sm "+branch+" btn-success\"><span class=\"glyphicon glyphicon-ok\" aria-hidden=\"true\"></span> Listed</button>" );
	} else {
		$("#"+id+'.'+branch).replaceWith( "<button id=\""+ id +"\" onclick='addtoqueue(\""+ id +"\", \""+ branch +"\")' class=\"btn btn-sm "+branch+" btn-default\"><span class=\"glyphicon glyphicon-remove\" aria-hidden=\"true\"></span> Unlisted</button>" );
	}

	// increase number on apply button
	var $number = $('#queue');
	$number.html((parseInt($number.html(),10) || 0) - 1);
	//alert(JSON.stringify(queue));
}

function sendqueue() {
	// alert(JSON.stringify(queue));
	$(".loading_modal").show();
	$.ajax({
	    url: '/updates/process_queue',
	    type: 'POST',
	    contentType: 'application/json; charset=utf-8',
	    data: JSON.stringify(queue),
	    dataType: 'text',
	    success: function(result) {
	        // alert(result.Result);
	        queue = [];
	        queueId = 0;
	        getdata();
	    }
	});
}

function getdata() {
	$(".loading_modal").show();

	cookie = getCookie("hidecommonly");
	if(cookie == "true") {
		$('#icon').replaceWith('<a href="#" id="icon" onclick="hidecommonly();"><span class="glyphicon glyphicon-remove" aria-hidden="true"></span> Unhide commonly updates</a>');
	} else {
		$('#icon').replaceWith('<a href="#" id="icon" onclick="hidecommonly();"><span class="glyphicon glyphicon-ok" aria-hidden="true"></span> Hide commonly updates</a>');
	}

	var manifestURL = '/updates/update_list';
	$.get(manifestURL, function(data) {
        $('#data').html(data);
        $(".loading_modal").hide();
        var $number = $('#queue');
		$number.html(0);  
    });

}

function addall(branchname) {
	$(".loading_modal").show();
	$.ajax({
	    url: '/updates/add_all/'+branchname,
	    type: 'POST',
	    contentType: 'application/json; charset=utf-8',
	    success: function(result) {
	        queue = [];
	        queueId = 0;
	        getdata();
	    }
	});
}

function copybranch(from, to) {
	$(".loading_modal").show();
	$.ajax({
	    url: '/updates/dup/'+from+'/'+to,
	    type: 'POST',
	    contentType: 'application/json; charset=utf-8',
	    success: function(result) {
	        queue = [];
	        queueId = 0;
	        getdata();
	    }
	});
}

function deletebranch(branchname) {
	$(".loading_modal").show();
	$.ajax({
	    url: '/updates/delete_branch/'+branchname,
	    type: 'POST',
	    contentType: 'application/json; charset=utf-8',
	    success: function(result) {
	        queue = [];
	        queueId = 0;
	        getdata();
	    }
	});
}

function findAndRemove(obj, prop, val) {
    var c, found=false;
    for(c in obj) {
        if(obj[c][prop] == val) {
            found=true;
            break;
        }
    }
    if(found){
        queue.splice(c,1);
    }
}

function showDiscr(element) {
	if($(element).find('.hidden').length != 0) {
		$(element).children(".well").removeClass("hidden");
	} else {
		$(element).children(".well").addClass("hidden");
	}
}

function newbranch(branch) {
	if(branch != "") {
		$(".loading_modal").show();
	$.ajax({
	    url: '/updates/new_branch/'+branch,
	    type: 'POST',
	    contentType: 'application/json; charset=utf-8',
	    success: function(result) {
	        queue = [];
	        queueId = 0;
	        getdata();
	    }
	});
	}
	
	$('#branch-name').val('');
} 

function hidecommonly() {
	cookie = getCookie("hidecommonly");
	if(cookie == "true") {
		document.cookie="hidecommonly=false";
	} else {
		document.cookie="hidecommonly=true";
	}
	getdata();
}

//
function initUpdatesTable() {
	var columns = dataTableCols('#list_items');
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
			if ( aData['depricated'] == "depricated" )
			{
				$('td', nRow).css('background-color', 'Red');
			}
		},
		"columns": columns,
		columnDefs: [
			{ targets: [1], "className": "left", },
			{ targets: [0], "className": 'details-control', "width": "auto" },
			{ targets: [1], "width": 50 },
			{ targets: [2], "width": 75 },
			{ "className": "text-center", "width": 20, "targets": "_all"},
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
	columns = $(id + ' thead tr th').map(function() { 
    	item = { "data": this.innerHTML.toLowerCase() };

		return item
  	}).get();;
	return columns
}

/* Formatting function for row details - modify as you need */
function format ( d ) {
    // `d` is the original data object for the row
	test = d.description
	test=test.replaceChild;
	alert(test)
    return d.key + '<br>' + test
}
