function do_resize() {
    $('#item_editor').height($(window).height() - 270);
    //ace editor is dumb and needs the height specifically as well
    $('#plist').height($(window).height() - 270);
    $('#item_list').height($(window).height() - 150);
}
$(window).resize(do_resize);

$(document).ready(function() {
    initManifestsTable();
    hash = window.location.hash;
    if (hash.length > 1) {
        getManifestItem(hash.slice(1));
    }
    getCatalogData();
    $('#listSearchField').focus();
    do_resize();

    $('#manifest_search_btn').click( function(){
        searchManifests();
    });
    //...or when they press the return key in the form field.
    $('#manifest-search-text').keydown( function(event){
      if(event.keyCode == 13) {
        // Prevent the browser from attempting to submit the form
        event.preventDefault();
        event.stopPropagation();
        searchManifests();
      }
    });

    // Submit the new manifest form when the user clicks the Create button...
    $('[data-new="manifest"]').click( function(){
        newManifestItem();
    });
    //...or when they press the return key in the form field.
    $('#new-manifest-name').keydown( function(event){
        if (event.keyCode == 13) {
            // Prevent the browser from attempting to submit the form
            event.preventDefault();
            event.stopPropagation();
            newManifestItem();
        }
    });

    // Note the use of $(document).on() below: This is to address the fact
    // that the DOM elements we want to listen to might not yet exist.

    // Submit the duplicate manifest form when the user clicks the Duplicate
    // button...
    $(document).on('click', '[data-copy="manifest"]', function(){
        duplicateManifestItem();
    });

    //...or when they press the return key in the form field.
    $(document).on('keydown', '#manifest-copy-name', function(event) {
        if (event.keyCode == 13) {
            // Prevent the browser from attempting to submit the form
            event.preventDefault();
            event.stopPropagation();
            duplicateManifestItem();
        }
    });

    // When a modal is shown, and it contains an <input>, make sure it's
    // selected when the modal is shown.
    $(document).on('shown.bs.modal', '.modal', function(event){
        $(event.currentTarget).find('input').select();
    });

    $(window).on('hashchange', function() {
        hash = window.location.hash;
        if (hash.length > 1) {
            if (hash.slice(1) != current_pathname) {
                getManifestItem(hash.slice(1));
            }
        }
    });
} );

function linkToIncludedManifest(target) {
    //parent is <td>; its parent is <tr>
    var tableRow = $(target).closest('tr'),
        manifest_path = $(tableRow).find('.value').val();
    getManifestItem(manifest_path);
}

var render_name = function(data, type, full, meta) {
    return '<a href="#' + data + '">' + data + '</a>';
}

function initManifestsTable() {
    $('#list_items').dataTable({
        ajax: {
            url: "/api/manifests/?api_fields=filename",
            data: function() {
                if ($('#manifest-search-text').val() == '') {
                    return {};
                } else {
                    var key = $('#manifest-search-section').val();
                    var value = $('#manifest-search-text').val();
                    var filter_terms = {};
                    filter_terms[key] = value;
                    return filter_terms;
                }
            },
            cache: false,
            dataSrc: function ( json ) {
                var data_rows = [];
                var column_rows = [];
                for ( var i=0 ; i < json.length ; i++ ) {
                    data_rows.push(json[i]['filename']);
                    column_rows.push([json[i]['filename']]);
                }
                // store these names for later auto-complete and validation use
                $('#data_storage').data('manifest_names', data_rows);
                // jQuery doesn't actually update the DOM; in order that we
                // can see what's going on, we'll also update the DOM item
                $('#data_storage').attr('data-manifest_names', data_rows);
                return column_rows;
            },
            complete: function(jqXHR, textStatus) {
                window.clearInterval(poll_loop);
                $('#process_progress').modal('hide');
            },
            global: false,
        },
        "fnRowCallback": function( nRow, aData, iDisplayIndex, iDisplayIndexFull ) {
            $('td', nRow).addClass('table-list-item');
		},
         "columnDefs": [
          { "targets": 0,
            "render": render_name,
          }],
         "sDom": "<t>",
         "bPaginate": false,
         "bInfo": false,
         "autoWidth": false,
         "bFilter": true,
         "bStateSave": false,
         "aaSorting": [[0,'asc']]
     });
     // start our monitoring timer loop
     monitor_manifest_list();
     // tie our search field to the table
     var thisTable = $('#list_items').DataTable();
     $('#listSearchField').keyup(function(){
          thisTable.search($(this).val()).draw();
     });

     $('#list_items').on('click', 'tbody td', function () {
         var id = $(this).find('a').attr('href');
         id = id.substring(1);
         var url = window.location.href;
         window.location.href = url + id;
     });
}

function monitor_manifest_list() {
    $('#process_progress_title_text').text('Getting manifest data...')
    $('#process_progress_status_text').text('Processing...')
    poll_loop = setInterval(function() {
            update_status('/manifests/__get_manifest_list_status');
        }, 1000);
}

function cancelEdit() {
    hideSaveOrCancelBtns();
    window.location.hash = '';
    current_pathname = "";
    $("#manifestItems").modal("hide");
}

var js_obj = {};
// these should be moved into their own file maybe so they can be edited
// seperately
var key_list = {'catalogs': 'Catalogs',
                'included_manifests': 'Included Manifests',
                'featured_items': 'Featured Items',
                'managed_installs': 'Managed Installs',
                'managed_uninstalls': 'Managed Uninstalls',
                'managed_updates': 'Managed Updates',
                'optional_installs': 'Optional Installs',
                };

// these should be moved into their own file maybe so they can be edited
// seperately
var keys_and_types = {'catalogs': ['catalogname'],
                      'conditional_items': [{'condition': 'os_vers_minor > 9',
                                             'managed_installs': ['itemname']}],
                      'included_manifests': ['manifestname'],
                      'featured_items': ['itemname'],
                      'managed_installs': ['itemname'],
                      'managed_uninstalls': ['itemname'],
                      'managed_updates': ['itemname'],
                      'optional_installs': ['itemname'],
                     };

function getCurrentCatalogList() {
    if ( js_obj.hasOwnProperty('catalogs') ) {
        return js_obj['catalogs'];
    } else {
        return [];
    }
}

function getSuggestedItems() {
    // return a list of item names based on current manifest catalog list
    var data = $('#data_storage').data('catalog_data');
    if (data) {
        var catalog_list = getCurrentCatalogList();
        if (catalog_list.length == 0) {
            // search all available catalogs
            catalog_list = Object.keys(data);
        }
        var suggested = [];
        for (var i=0, l=catalog_list.length; i<l; i++) {
            var catalog_name = catalog_list[i];
            if ( data.hasOwnProperty(catalog_name) ) {
                if ( data[catalog_name].hasOwnProperty('suggested') ) {
                    Array.prototype.push.apply(suggested, data[catalog_name]['suggested']);
                }
            }
        }
        return uniques(suggested);
    } else {
        return [];
    }
}

function getValidCatalogNames() {
    // return a list of valid catalog names, which are the keys to the
    // catalog_data object minus those keys that start with "._"
    var data = $('#data_storage').data('catalog_data');
    if (data) {
        var raw_names = Object.keys(data);
        // in Python this would be
        // return [item for item in raw_names if not item.startswith('._')]
        return raw_names.filter(function(x){return (x.substring(0, 2) != "._")})
    }
    return [];
}

function getValidInstallItems() {
    // return a list of item names based on current manifest catalog list
    var data = $('#data_storage').data('catalog_data');
    if (data) {
        var catalog_list = getCurrentCatalogList();
        if (catalog_list.length == 0) {
            // search all available catalogs
            catalog_list = Object.keys(data);
        }
        var valid = [];
        for (var i=0, l=catalog_list.length; i<l; i++) {
            var catalog_name = catalog_list[i];
            if ( data.hasOwnProperty(catalog_name) ) {
                Array.prototype.push.apply(valid, data[catalog_name]['suggested']);
                Array.prototype.push.apply(valid, data[catalog_name]['updates']);
                Array.prototype.push.apply(valid, data[catalog_name]['with_version']);
            }
        }
        return uniques(valid);
    } else {
        return [];
    }
}

var validator = function(path, val) {
    // returns a bootstrap class name to highlight items that aren't 'valid'
    var path_items = path.split('.');
    if (path_items.indexOf('catalogs') != -1) {
        //check val against valid catalog names
        var data = $('#data_storage').data('catalog_data');
        var catalog_names = Object.keys(data);
        if (catalog_names && catalog_names.indexOf(val) == -1) return 'table-warning';
    }
    if (path_items.indexOf('included_manifests') != -1) {
        //check val against valid manifest names
        var manifest_names = $('#data_storage').data('manifest_names');
        if (manifest_names && manifest_names.indexOf(val) == -1) return 'table-warning';
    }
    if (path_items.indexOf('featured_items') != -1 ||
        path_items.indexOf('managed_installs') != -1 ||
        path_items.indexOf('managed_uninstalls') != -1 ||
        path_items.indexOf('managed_updates') != -1 ||
        path_items.indexOf('optional_installs') != -1) {
            //check val against valid install items
            var valid_names = getValidInstallItems();
            if (valid_names.length && valid_names.indexOf(val) == -1) {
                return 'table-warning';
            }
    }
    return null;
};

function setupHelpers() {

}

function setupView(viewName) {
    selected_tab_viewname = viewName;
    if (viewName == '#basicstab') {
        constructBasics();
    } else if (viewName == '#detailtab') {
        constructDetail();
    } else if (viewName == '#plisttab') {
        editor.focus();
        editor.resize(true);
    }
}

function constructBasics() {
    if (js_obj != null) {
        $('#basics').html('')
        $('#basics').plistEditor(js_obj,
            { change: updatePlistAndDetail,
              keylist: key_list,
              keytypes: keys_and_types,
              validator: validator});
    } else {
        $('#basics').html('<br/>Invalid plist.')
    }
    setupHelpers();
    addIncludedManifestLinks('#basics');
}

function constructDetail() {
    if (js_obj != null) {
        $('#detail').html('')
        $('#detail').plistEditor(js_obj,
            { change: updatePlistAndBasics,
                keytypes: keys_and_types,
                validator: validator});
    } else {
        $('#detail').html('<br/>Invalid plist.')
    }
    setupHelpers();
    addIncludedManifestLinks('#detail');
}

function addIncludedManifestLinks(editor) {
    rows = $(editor).find("tr[data-bs-path='included_manifests']");
    $(rows).each(function() {
        var row_controls = $(this).find('.row-controls');
        $(row_controls).each(function() {
            var tableRow = $(this).closest('tr'),
                manifest_path = $(tableRow).find('.value').val();
            //alert(manifest_path);
            //var link_btn = $('<span>',
            //                 {'class': 'row_link_btn glyphicon glyphicon-circle-arrow-right'});
            var link_btn = $('<a href="#' + manifest_path + '"><i class="row_link_btn fa fa-arrow-circle-right"/></a>')
            $(this).append(link_btn);
        });
    });
}

function updatePlist() {
    if (js_obj != null) {
        editor.setValue(PlistParser.toPlist(js_obj, true));
        editor.selection.clearSelection();
        editor.selection.moveCursorToPosition({row: 0, column: 0});
        editor.selection.selectFileStart();
    }
}

function updatePlistAndBasics(data) {
    js_obj = data;
    showSaveOrCancelBtns();
    updatePlist();
    setupHelpers();
}

function updatePlistAndDetail(data) {
    js_obj = data;
    showSaveOrCancelBtns();
    updatePlist();
    setupHelpers();
}

function plistChanged() {
    showSaveOrCancelBtns();
    var val = editor.getValue();
    if (val) {
        try { js_obj = PlistParser.parse(val); }
        catch (e) {
            //alert('Error in parsing plist. ' + e);
            js_obj = null;
        }
    } else {
        js_obj = {};
    }
}

var current_pathname = "";
var requested_pathname = "";
var selected_tab_viewname = "#basicstab";
var editor = null;

function getManifestItem(pathname) {
    if ($('#save_and_cancel').length && !$('#save_and_cancel').hasClass('d-none')) {
        requested_pathname = pathname;
        $("#saveOrCancelConfirmationModal").modal("show");
        event.preventDefault();
        return;
    }
    var manifestItemURL = '/manifests/' + pathname;
    $.ajax({
        method: 'GET',
        url: manifestItemURL,
        timeout: 10000,
        cache: false,
        success: function(data) {
            $('#manifest_detail').html(data);
            val = $('#plist').text();
            try { js_obj = PlistParser.parse(val); }
            catch (e) {
                //alert('Error in parsing plist. ' + e);
                js_obj = null;
            }
            $('button[data-bs-toggle="tab"]').on('click', function (e) {
                //e.target // newly activated tab
                //e.relatedTarget // previous active tab
                setupView('#'+e.target.id);
            });
            editor = initializeAceEditor('plist', plistChanged);
            hideSaveOrCancelBtns();
            detectUnsavedChanges();
            current_pathname = pathname;
            requested_pathname = "";
            $('#editortabs a[href="' + selected_tab_viewname + '"]').tab('show');
            setupView(selected_tab_viewname);
            do_resize();
            window.history.replaceState({'manifest_detail': data}, manifestItemURL, '/manifests/');
            window.location.hash = pathname;

            if (!$('#manifestItems').hasClass('in')){
              //alert("test")
              $("#manifestItems").modal("show");
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $('#manifest_detail').html("")
            current_pathname = "";
            $("#errorModalTitleText").text("Manifest read error");
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
        dataType: 'html'
    });
}


function duplicateManifestItem() {
    var manifest_names = $('#data_storage').data('manifest_names');
    var pathname = $('#manifest-copy-name').val();
    if (manifest_names.indexOf(pathname) != -1) {
        alert('That manifest name is already in use!');
        $('#manifest-copy-name').select();
        return;
    }
    $('#copyManifestModal').modal('hide');
    $('.modal-backdrop').remove();
    $('#manifest-copy-name').val("");
    var manifestItemURL = '/api/manifests/' + pathname;
    var plist_data = editor.getValue();

    $.ajax({
        method: 'POST',
        url: manifestItemURL,
        headers: {'Content-Type': 'application/xml',
                  'Accept': 'application/xml'},
        data: plist_data,
        timeout: 10000,
        cache: false,
        success: function(data) {
            $('#list_items').DataTable().ajax.reload();
            getManifestItem(pathname);
            //window.location.hash = pathname;
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $("#errorModalTitleText").text("Manifest creation error");
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


function saveManifestItem() {
    var plist_data = editor.getValue();
    //var postdata = JSON.stringify({'plist_data': plist_data})
    var manifestItemURL = '/api/manifests/' + current_pathname;
    $.ajax({
        method: 'POST',
        url: manifestItemURL,
        headers: {'X-METHODOVERRIDE': 'PUT',
                  'Content-Type': 'application/xml',
                  'Accept': 'application/xml'},
        data: plist_data,
        timeout: 10000,
        success: function(data) {
            hideSaveOrCancelBtns();
            $("#manifestItems").modal("hide");
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $("#errorModalTitleText").text("Manifest save error");
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

function searchManifests() {
    $('#searchManifestModal').modal('hide');
    $('.modal-backdrop').remove();
    $('#list_items').DataTable().destroy()
    initManifestsTable();
}

function newManifestItem() {
    var manifest_names = $('#data_storage').data('manifest_names');
    var pathname = $('#new-manifest-name').val();
    if (manifest_names.indexOf(pathname) != -1) {
        alert('That manifest name is already in use!');
        $('#new-manifest-name').select();
        return;
    }
    $('#newManifestModal').modal('hide');
    $('.modal-backdrop').remove();
    $('#new-manifest-name').val("");
    var manifestItemURL = '/api/manifests/' + pathname;

    $.ajax({
        method: 'POST',
        url: manifestItemURL,
        timeout: 10000,
        cache: false,
        success: function(data) {
            $('#list_items').DataTable().ajax.reload();
            getManifestItem(pathname);
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $("#errorModalTitleText").text("Manifest creation error");
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

function deleteManifestItem(manifest_name) {
    $('.modal-backdrop').remove();
    var manifestItemURL = '/api/manifests/' + manifest_name;
    $.ajax({
        method: 'POST',
        url: manifestItemURL,
        headers: {'X-METHODOVERRIDE': 'DELETE'},
        success: function(data) {
            hideSaveOrCancelBtns();
            window.location.hash = '';
            $('#manifest_detail').html('');
            $('#list_items').DataTable().ajax.reload();
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $("#errorModalTitleText").text("Manifest delete error");
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
    });;
}
