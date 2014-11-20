// --------- edit Software ----------------------------------

$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    var cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))){
        // Only send the token to relative URLs i.e. locally.
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

function deleteManifest() {
  var manifest_name = $('.manifest_name').attr('id');
  location.href='/manifest/delete/' + manifest_name.replace(/\//g, ':');
}

function cleanDetailPane() {
  // unbind any existing event handlers for the detail pane
    $('.editable').off('dblclick');
    $('.lineitem_delete').off('click');

    // destroy sortability for existing elements
    //$('.catalogs_section').sortable('destroy');
    //$('.included_manifests_section').sortable('destroy');
    //$('.section').sortable('destroy');
    
    // clear detail pane
    // $('#detail').html('<div></div>')
}

var inEditMode = false;
function makeEditableItems(manifest_name, serial) {
    // grab autocomplete data from document
    var autocomplete_data = $('#data_storage').data('autocomplete_data');
    // make sections sortable and drag/droppable
    //$('#managed_installs').sortable();
    $('.row').removeClass("hidden");
    $('.catalogs_section').sortable();
    $('.included_manifests_section').sortable();
    $('.section').sortable({
        connectWith: '.section'
    });
    //replace <a> links with 'editable' divs
    $('.entrys').children($('a')).each(function(){
        var item = "<div class='editable'>" + $(this).parent().attr('id') + "</div>";
        $(this).replaceWith(item);
    });
    $('.entrys').append("<span class='btn btn-danger lineitem_delete pull-right' style='margin-top:-16px;'></span>");
    $('.sw_entrys').append("<span class='btn btn-danger sw_delete pull-right' style='margin-top:4px;'></span>");
    $('.manifest_section').on('dblclick', '.editable', function() {
        makeEditableItem(manifest_name, autocomplete_data, $(this));
    });
    $('.manifest_section').on('click', '.lineitem_delete', function() {
      if ($(this).parent().attr('id')) {    
        var r = confirm("Really delete " + $(this).parent().attr('id') + " from " + $(this).parent().parent().attr('id') + "?");
        if (r == true){ $(this).parent().remove(); };
      } else {
          $(this).parent().remove();
      }
    });
    $('.manifest_section').on('click', '.sw_delete', function() {
      if ($(this).parent().parent().attr('id')) {    
        var r = confirm("Really delete " + $(this).parent().parent().attr('id') + " from " + $(this).parent().parent().parent().parent().attr('id') + "?");
        if (r == true){ $(this).parent().parent().remove(); };
      } else {
          $(this).parent().parent().remove();
      }
    });
    $('.section_label').append("<a class='btn btn-success btn-mini add_item pull-right' href='#' style='margin-top:-20px;'></a>");
    $('.add_item').click(function() {
        var list_item = $("<li class='list-group-item entrys'><span class='btn btn-danger btn-mini lineitem_delete pull-right' style='margin-top:4px;'></span><div class='editable'></div></li>");
        $(this).parent().siblings($('ul')).append(list_item);   
        makeEditableItem(manifest_name, autocomplete_data, list_item.children(".editable"));
    });

    $('.section_label_software').append("<a class='btn btn-success btn-mini add_software pull-right' href='#'></a>");
    $('.add_software').click(function() {
        var list_item = $("<tr><td></td><td><div class='editable'></div></td><td></td><td></td><td><span class='btn btn-danger btn-mini sw_delete pull-right' style='margin-top:6px;'></span></td></tr>");
        $(this).parent().siblings($('tbody')).append(list_item);
        makeEditableItem(manifest_name, autocomplete_data, list_item.children($('tr')).children(".editable"));
    });

    $('.edit').val('Save').unbind('click').click(function() {
        getManifestDetailFromDOMAndSave();
    });
    $('#save_and_cancel').append("<input type='button' class='cancel btn btn-default' value='Cancel' onClick='cancelEdit(\"" + manifest_name + "\", \"" + serial + "\")'></input>");
    $(window).bind('beforeunload', function(){
        return "Changes will be lost!";
    });
    inEditMode = true;
}

function updateLineItem(item) {
    var text_value = item.val();
    if (text_value.length) {
        if (item.parent().parent().parent().attr('id') == "managed_installs" || item.parent().parent().parent().attr('id') == "optional_installs" || item.parent().parent().parent().attr('id') == "managed_uninstalls") {
            item.parent().parent().attr('id', text_value);
        } else {
            item.parent().attr('id', text_value);
        }
        var new_div = $("<div class='editable'>" + text_value + "</div>")
        item.replaceWith(new_div);
    } else {
        item.parent().remove();
    }
}

function makeEditableItem(manifest_name, autocomplete_data, editable_div) {
    // commit any existing active lineiteminput
    $('.lineiteminput').each(function(){updateLineItem($(this))});

    var text_value = editable_div.text();
    var input_box = $("<input type='text' id='" + text_value + "' class='lineiteminput' value='" + text_value + "' />");
    var grandparent_id = editable_div.parent().parent().attr('id');
    var kind = 'items';
    if (grandparent_id == 'catalogs') {
      kind = 'catalogs';
    } else if (grandparent_id == 'included_manifests') {
      kind = 'manifests';
    }
    editable_div.replaceWith(input_box);
    input_box.typeahead({source: autocomplete_data[kind]})
    input_box.focus();
    input_box.bind('keyup', function(event) {
        if (event.which == '13' || event.which == '9') {
            event.preventDefault();
            updateLineItem($(this));
        } else if (event.which == '27') {
            event.preventDefault();
            $(this).val($(this).attr('id'));
            updateLineItem($(this));
        }
    });
}

function cancelEdit(manifest_name, serial, manifest_name) {
    inEditMode = false;
    $(window).unbind("beforeunload");
    getDetail("Manifest", serial);
}

function getManifestSectionArray(section_name) {
    // gets array elements from manifest section
    // returns an array
    // section_name is the JQuery class descriptor
    the_array = [];
    if (section_name == "#managed_installs" || section_name == "#optional_installs" ) {
        $(section_name).children().each(function(){
            var item = $(this).attr('id');
            if (item) { the_array.push(item); };
        });
    } else {
        $(section_name).children($('li')).each(function(){
            var item = $(this).attr('id'); 
            alert   
            if (item) { the_array.push(item); };
        });
    }
    return the_array;
}

function getManifestDetailFromDOMAndSave() {
    // reads elements from the DOM to build up a JSON object
    // describing the manifest post-edit
    // then POSTs to server
    
    //
    $("#imgProgress").show();
    
    //unbind beforeunload
    inEditMode = false;
    $(window).unbind("beforeunload");
    
    // commit any existing active lineiteminput
    $('.lineiteminput').each(function(){updateLineItem($(this))});
    
    var manifest = {};
    var manifest_name = $('.manifest_name').attr('id');
    $('#manifest_detail').children($('manifest_section')).children($('ul')).each(function() {
        section_name = $(this).attr('id');
        if (section_name) {
          manifest[section_name] = getManifestSectionArray('#' + section_name);
        }
    });
    $('#managed_installs').each(function() {
        section_name = $(this).attr('id');
        if (section_name) {
          manifest[section_name] = getManifestSectionArray('#' + section_name);
        }
    });
    $('#optional_installs').each(function() {
        section_name = $(this).attr('id');
        if (section_name) {
          manifest[section_name] = getManifestSectionArray('#' + section_name);
        }
    });
    $('#managed_uninstalls').each(function() {
        section_name = $(this).attr('id');
        if (section_name) {
          manifest[section_name] = getManifestSectionArray('#' + section_name);
        }
    });
    var postdata = JSON.stringify(manifest)
    var postURL = '/manifest/detail/' + manifest_name.replace(/\//g, ':');
    //alert(postdata);
    //console.log(postdata);
    $.ajax({
      type: 'POST',
      url: postURL,
      data: postdata,
      success: function(data) {
        //alert("SUCCESS: " + data);
        getDetail("Manifest");
      },
      error: function(jqXHR, textStatus, errorThrown) {
        $("#imgProgress").hide();
        alert("ERROR: " + textStatus + "\n" + errorThrown);
      },
      dataType: 'json'
    });
}

function getDetail(type, serial, manifest_name) {
    if (inEditMode) {
        if (! confirm('Discard current changes?')) {
            event.preventDefault();
            return;
        }
        inEditMode = false;
        $(window).unbind("beforeunload");
    }
    switch (type) {
        case "Inventory":
            enableSearch();
            var manifestURL = '/inventory/detail/' + serial;
            break;

        case "Machine":
            diableSearch();
            // get new detail for the pane
            var manifestURL = '/update/detailmachine/' + serial;
            break;

        case "Manifest":
            if (!manifest_name) {
                var manifest_name = $('.manifest_name').attr('id');
            };
            if (!serial) {
                var serial = $('.serial_number').attr('id');
            };
            cleanDetailPane();
            diableSearch();
            var manifestURL = '/update/detailpkg/' + manifest_name.replace(/\//g, ':') + "/" + serial;
            break;

        case "AppleUpdates":
            diableSearch();
            var manifestURL = '/update/appleupdate/' + serial;
            break;
    }
    $("#imgProgress").show();
    // get new detail for the pane
    $.get(manifestURL, function(data) {
        $('#data').html(data);
        if(type == "Manifest") {
            $('.edit').click(function(){
                makeEditableItems(manifest_name, serial);
            });
        }
        activeButton(type);
        $("#imgProgress").hide();
    });
}

function diableSearch() {
    $('#SearchFieldMobile').prop('disabled', true);
    $('#SearchField').prop('disabled', true);
}

function enableSearch() {
    $('#SearchFieldMobile').prop('disabled', false);
    $('#SearchField').prop('disabled', false);
    document.getElementById("SearchField").select();
}

function activeButton(id) {
    $('.buttons[id="' + id + '"]').addClass('active');
    $('.buttons[id!="' + id + '"]').removeClass('active');
}

function sideSecific() {
}

// ---------------------------------------------------------------------------
