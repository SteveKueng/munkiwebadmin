function do_resize() {
    $('#item_list').height($(window).height() - 150);
}

$(window).resize(do_resize);
var file;

// reset url on modal close
$(document).on('hide.bs.modal','#iconItem', function () {
  // check for unsaved changes
  if ($('#save_and_cancel').length && !$('#save_and_cancel').hasClass('hidden')) {
      ($('#iconItem').data('bs.modal') || {})._isShown = false;
      $("#saveOrCancelConfirmationModal").modal("show");
      event.preventDefault();
      return;
  } else {
    ($('#iconItem').data('bs.modal') || {})._isShown = true;
  }
});

$(document).ready(function() {
    initIconsTable();
    hash = window.location.hash;
    if (hash.length > 1) {
        getIconItem(hash.slice(1));
    }
    $('#listSearchField').focus();
    do_resize();
    $(window).on('hashchange', function() {
        hash = window.location.hash;
        if (hash.length > 1) {
            if (hash.slice(1) != current_pathname) {
                getIconItem(hash.slice(1));
            }
        }
    });
} );

var render_name = function(data, type, row, meta) {
    return '<a href="#'+row+'">'+row+'</a>';
}

var render_icon = function(data, type, row, meta) {
    return '<img src="/api/icons/' + row +'" alt="" width="20"  onerror=\'this.src="/static/img/GenericPkg.png";\'>';
}

function initIconsTable() {
    $('#list_items').dataTable({
        ajax: {
            url: "/api/icons",
            cache: false,
            dataSrc: function ( json ) {
                var column_rows = [];
                for ( var i=0 ; i < json.length; i++ ) {
                    if(json[i] != "_icon_hashes.plist") {
                        column_rows.push(json[i]);
                    }
				}
                return column_rows;
            },
            complete: function(jqXHR, textStatus){
                  window.clearInterval(poll_loop);
                  $("#item-count-badge").text(jqXHR.responseJSON.length);
                },
            global: false,
        },
        columnDefs: [{
            "targets": 0,
            "render": render_icon,
            "searchable": false,
        },
        {
            "targets": 1,
            "render": render_name,
        },],
        'sDom': '"top"i',
        "paging":false,
        "scrollY": 'calc(100vh - 350px)',
        "scrollCollapse": true,
        "bFilter": true,
        "bStateSave": true,
        "aaSorting": [[0,'asc']]
        });
        // start our monitoring timer loop
        monitor_icon_list();
        // tie our search field to the table
        var thisTable = $('#list_items').DataTable(),
        searchField = $('#listSearchField');
        searchField.keyup(function(){
            thisTable.search($(this).val()).draw();
        });
}


function cancelEdit() {
    hideSaveOrCancelBtns();
    window.location.hash = '';
    current_pathname = "";
    $("#iconItem").modal("hide");
}


function rebuildCatalogs() {
    $('#process_progress_title_text').text('Rebuilding catalogs...')
    $('#process_progress_status_text').text('Processing...')
    $('#process_progress').modal('show');
    poll_loop = setInterval(function() {
            update_status('/makecatalogs/status');
        }, 1000);
    $.ajax({
        type: 'POST',
        url: '/makecatalogs/run',
        data: '',
        dataType: 'json',
        global: false,
        complete: function(jqXHR, textStatus){
            window.clearInterval(poll_loop);
            $('#process_progress').modal('hide');
            $('#list_items').DataTable().ajax.reload();
        },
    });
}

function monitor_icon_list() {
    $('#process_progress_title_text').text('Getting icons...')
    $('#process_progress_status_text').text('Processing...')
    poll_loop = setInterval(function() {
            update_status('/icons/__get_process_status');
        }, 1000);
}

function showDeleteConfirmationModal() {
    // show the deletion confirmation dialog
    $("#deleteConfirmationModal").modal("show");
}


function deleteIconItem() {
    // do the actual icon item deletion
    $('.modal-backdrop').remove();
    var iconItemURL = '/api/icons/' + current_pathname;
    $.ajax({
        type: 'DELETE',
        url: iconItemURL,
        success: function(data) {
            rebuildCatalogs();
            window.location.hash = '';
            $('#iconItem').modal("hide");
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $("#errorModalTitleText").text("Pkginfo delete error");
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

var current_pathname = "";
var requested_pathname = "";

function getIconItem(pathname) {
    if ($('#save_and_cancel').length && !$('#save_and_cancel').hasClass('hidden')) {
        requested_pathname = pathname;
        $("#saveOrCancelConfirmationModal").modal("show");
        event.preventDefault();
        return;
    }
    hideSaveOrCancelBtns();
    detectUnsavedChanges();
    $('#pathname').text(pathname.replace(/%20/g, " "));
    $("#iconImg").prop("src", "/api/icons/" + pathname);
    $("#iconImg").prop("alt", pathname);

    $("#inputIconName").prop("value", pathname.replace(/%20/g, " "));
    current_pathname = pathname;
    requested_pathname = "";
    do_resize();
    window.location.hash = pathname;
    if (!$('#iconItem').hasClass('in')){
        $("#iconItem").modal("show");
    }
}

function uploadIcon() {
    var name = $("#new-icon-name").val()
    var iconItemURL = '/api/icons/' + name;
    var file = $("#previewImg").attr('src');
    $.ajax({
        type: 'PUT',
        url: iconItemURL,
        data: "img="+file,
        timeout: 10000,
        processData: false,
        success: function(data) {
            rebuildCatalogs();
            $("#newIconModal").modal("hide");
            $("#previewImg").prop("src", "/static/img/imgPlaceholder.png");
            $("#new-icon-name").val("");
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $("#errorModalTitleText").text("Icons write error");
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

function previewFile(elem){
    var reader  = new FileReader();
    reader.onloadend = function () {
        $("#previewImg").prop("src", reader.result);
    }

    if (elem.files[0]) {
        file = elem.files[0];
        reader.readAsDataURL(elem.files[0]); //reads the data as a URL
        $("#new-icon-name").val(elem.files[0].name)
    }
}